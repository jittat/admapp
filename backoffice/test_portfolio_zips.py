# -*- coding: utf-8 -*-
"""Tests for backoffice.portfolio_zips (bulk portfolio zips uploaded to S3)."""
import csv
import io
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase, override_settings

from backoffice import portfolio_zips as pz


class FakeS3:
    """Just enough of a boto3 S3 client for multipart uploads."""

    def __init__(self, fail_on_complete=None):
        self.uploads = {}
        self.objects = {}
        self.part_sizes = {}
        self.aborted = []
        self.deleted = []
        self.fail_on_complete = fail_on_complete
        self.completed = 0

    def create_multipart_upload(self, Bucket, Key, ContentType):
        upload_id = f'upload-{len(self.uploads) + len(self.objects) + len(self.aborted) + 1}'
        self.uploads[upload_id] = {'key': Key, 'parts': {}}
        return {'UploadId': upload_id}

    def upload_part(self, Bucket, Key, UploadId, PartNumber, Body):
        self.uploads[UploadId]['parts'][PartNumber] = Body
        return {'ETag': f'"etag-{PartNumber}"'}

    def complete_multipart_upload(self, Bucket, Key, UploadId, MultipartUpload):
        self.completed += 1
        if self.fail_on_complete == self.completed:
            raise RuntimeError('upload failed')
        parts = self.uploads.pop(UploadId)['parts']
        numbers = [p['PartNumber'] for p in MultipartUpload['Parts']]
        self.part_sizes[Key] = [len(parts[n]) for n in numbers]
        self.objects[Key] = b''.join(parts[n] for n in numbers)

    def abort_multipart_upload(self, Bucket, Key, UploadId):
        self.uploads.pop(UploadId)
        self.aborted.append(Key)

    def delete_object(self, Bucket, Key):
        self.deleted.append(Key)
        self.objects.pop(Key, None)


def applicant(national_id='1234567890123', first_name='สมชาย', last_name='ใจดี'):
    return SimpleNamespace(national_id=national_id,
                           first_name=first_name, last_name=last_name)


class FileNameTestCase(SimpleTestCase):

    def test_keeps_thai_vowels_and_tone_marks(self):
        self.assertEqual(pz.safe_filename_part('สมชาย'), 'สมชาย')
        self.assertEqual(pz.safe_filename_part('ณัฐพงษ์'), 'ณัฐพงษ์')

    def test_removes_invisible_and_invalid_characters(self):
        self.assertEqual(pz.safe_filename_part('สม​ชาย﻿'), 'สมชาย')
        self.assertEqual(pz.safe_filename_part('a/b\\c:d*e?f"g<h>i|j'), 'abcdefghij')
        self.assertEqual(pz.safe_filename_part('line\nbreak\ttab'), 'line_break_tab')

    def test_spaces_become_underscores_and_ends_are_trimmed(self):
        self.assertEqual(pz.safe_filename_part('  Mary   Ann  '), 'Mary_Ann')
        self.assertEqual(pz.safe_filename_part('...name.. '), 'name')

    def test_empty_and_long(self):
        self.assertEqual(pz.safe_filename_part(None), '')
        self.assertEqual(pz.safe_filename_part('​?*'), '')
        self.assertEqual(len(pz.safe_filename_part('ก' * 200)), 80)

    def test_applicant_file_base(self):
        self.assertEqual(pz.applicant_file_base(7, applicant()),
                         '007_1234567890123_สมชาย_ใจดี')
        self.assertEqual(pz.applicant_file_base(7, applicant(first_name='Mary Ann',
                                                             last_name='Smith')),
                         '007_1234567890123_Mary_Ann_Smith')
        self.assertEqual(pz.applicant_file_base(1234, applicant(), seq_width=4)[:5],
                         '1234_')

    def test_applicant_file_base_without_name(self):
        self.assertEqual(pz.applicant_file_base(1, applicant(first_name='', last_name='?')),
                         '001_1234567890123_noname')
        self.assertEqual(pz.applicant_file_base(1, applicant(last_name='')),
                         '001_1234567890123_สมชาย')

    def test_zip_entry_name(self):
        self.assertEqual(pz.zip_entry_name('001_x', 1, '.pdf'), '001_x.pdf')
        self.assertEqual(pz.zip_entry_name('001_x', 2, '.pdf'), '001_x_2.pdf')

    def test_file_extension(self):
        self.assertEqual(pz.file_extension('documents/a/b/Port Folio.PDF'), '.pdf')
        self.assertEqual(pz.file_extension('noext'), '')
        self.assertEqual(pz.file_extension('x.p"d f'), '.pdf')

    def test_object_key(self):
        key = pz.object_key_for(SimpleNamespace(id=12), SimpleNamespace(id=3),
                                SimpleNamespace(number=7), '20261023-090000', 2)
        self.assertEqual(key, '12/3/major-007/20261023-090000/batch-02.zip')

    def test_make_batches_numbers_across_major(self):
        batches = pz.make_batches(['a', 'b', 'c', 'd', 'e'], 2)
        self.assertEqual(batches, [[(1, 'a'), (2, 'b')], [(3, 'c'), (4, 'd')], [(5, 'e')]])
        self.assertEqual(pz.make_batches([], 2), [])

    def test_seq_width(self):
        self.assertEqual(pz.seq_width_for(900), 3)
        self.assertEqual(pz.seq_width_for(1200), 4)


@override_settings(LOCAL_DOCUMENT_BASE_URL='https://example.com/folio/',
                   LOCAL_DOCUMENT_BASE_PATH='/data/folio')
class MirrorPathTestCase(SimpleTestCase):

    def test_url_under_base_url(self):
        self.assertEqual(pz.mirror_local_path('https://example.com/folio/123-abc.pdf'),
                         '/data/folio/123-abc.pdf')

    def test_other_urls_are_rejected(self):
        for url in ['https://other.com/folio/123.pdf',
                    'https://example.com/folio/',
                    'https://example.com/folio/../secret',
                    'https://example.com/folio/sub/123.pdf',
                    'https://example.com/folio/..',
                    '']:
            self.assertIsNone(pz.mirror_local_path(url), url)

    @override_settings(LOCAL_DOCUMENT_BASE_PATH='')
    def test_unconfigured(self):
        self.assertIsNone(pz.mirror_local_path('https://example.com/folio/123.pdf'))


class S3MultipartWriterTestCase(SimpleTestCase):

    def test_splits_into_parts_and_completes(self):
        client = FakeS3()
        writer = pz.S3MultipartWriter(client, 'bucket', 'k.zip', part_size=10)
        writer.write(b'a' * 7)
        writer.write(b'b' * 15)
        writer.write(b'c' * 3)
        writer.complete()

        self.assertEqual(client.part_sizes['k.zip'], [10, 10, 5])
        self.assertEqual(client.objects['k.zip'], b'a' * 7 + b'b' * 15 + b'c' * 3)
        self.assertEqual(writer.size, 25)

    def test_zip_written_through_writer_is_valid(self):
        client = FakeS3()
        writer = pz.S3MultipartWriter(client, 'bucket', 'k.zip', part_size=64)
        with zipfile.ZipFile(writer, 'w', compression=zipfile.ZIP_STORED) as zf:
            zf.writestr('สมชาย.pdf', b'x' * 500)
        writer.complete()

        with zipfile.ZipFile(io.BytesIO(client.objects['k.zip'])) as zf:
            self.assertEqual(zf.namelist(), ['สมชาย.pdf'])
            self.assertEqual(zf.read('สมชาย.pdf'), b'x' * 500)
            self.assertIsNone(zf.testzip())

    def test_abort(self):
        client = FakeS3()
        writer = pz.S3MultipartWriter(client, 'bucket', 'k.zip')
        writer.abort()
        self.assertEqual(client.aborted, ['k.zip'])
        self.assertEqual(client.uploads, {})


class BuildMajorZipsTestCase(TestCase):
    """End to end through the DB: applicants, payments, uploaded documents,
    the zips in a fake S3 and the PortfolioZipFile rows."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = tempfile.mkdtemp()
        cls.mirror_root = tempfile.mkdtemp()
        cls.settings_override = override_settings(
            MEDIA_ROOT=cls.media_root,
            LOCAL_DOCUMENT_BASE_PATH=cls.mirror_root,
            LOCAL_DOCUMENT_BASE_URL='https://example.com/folio',
            S3_PORTFOLIO_EXPIRY_DAYS=30)
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)
        shutil.rmtree(cls.mirror_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        from appl.models import (AdmissionProject, AdmissionProjectRound, AdmissionRound,
                                 Campus, Faculty, Major, ProjectUploadedDocument)

        self.admission_round = AdmissionRound.objects.create(
            number=1, rank=1, is_available=True,
            acceptance_result_date=datetime.now().date())
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test', base_fee=400,
            max_num_selections=1)
        AdmissionProjectRound.objects.create(
            admission_project=self.project, admission_round=self.admission_round,
            is_started=True,
            applying_deadline=datetime.now() + timedelta(days=7),
            payment_deadline=(datetime.now() + timedelta(days=10)).date())
        campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        faculty = Faculty.objects.create(title='Engineering', campus=campus)
        self.major = Major.objects.create(
            number=7, title='วิศวกรรมคอมพิวเตอร์', faculty=faculty,
            admission_project=self.project, slots=10, detail_items_csv='')
        self.other_major = Major.objects.create(
            number=8, title='วิศวกรรมไฟฟ้า', faculty=faculty,
            admission_project=self.project, slots=10, detail_items_csv='')
        self.pud = ProjectUploadedDocument.objects.create(
            rank=1, title='Portfolio', descriptions='', specifications='PDF',
            allowed_extentions='pdf', document_type='any',
            can_have_multiple_files=True, document_key='portfolio')
        self.pud.admission_projects.add(self.project)

        self.client_s3 = FakeS3()
        self.backup = {}

    # -- fixtures --

    def make_applicant(self, national_id, first_name, last_name, paid=True, major=None):
        from appl.models import MajorSelection, Payment
        from regis.models import Applicant

        a = Applicant.objects.create(national_id=national_id, prefix='นาย',
                                     first_name=first_name, last_name=last_name,
                                     email=f'{national_id}@test.com')
        application = a.apply_to_project(self.project, self.admission_round)
        MajorSelection.objects.create(
            applicant=a, project_application=application,
            admission_project=self.project, admission_round=self.admission_round,
            major_list=str((major or self.major).number), num_selected=1)
        if paid:
            Payment.objects.create(
                applicant=a, admission_round=self.admission_round,
                national_id=national_id, verification_number='x',
                amount=400, paid_at=datetime.now())
        return a

    def add_file(self, a, name, content, rank=0, on_disk=True):
        from appl.models import UploadedDocument

        stored = f'documents/applicant_{a.id}/doc_{self.pud.id}/{name}'
        if on_disk:
            path = os.path.join(self.media_root, stored)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(content)
        d = UploadedDocument.objects.create(applicant=a, project_uploaded_document=self.pud,
                                            rank=rank, uploaded_file=stored,
                                            original_filename=f'orig-{name}')
        if not on_disk:
            self.backup[d.id] = content
        return d

    def add_link(self, a, url, mirror_name=None, mirror_content=None, rank=0):
        from appl.models import UploadedDocument

        local_url = ''
        if mirror_name:
            local_url = f'https://example.com/folio/{mirror_name}'
            if mirror_content is not None:
                with open(os.path.join(self.mirror_root, mirror_name), 'wb') as f:
                    f.write(mirror_content)
        return UploadedDocument.objects.create(applicant=a, project_uploaded_document=self.pud,
                                               rank=rank, document_url=url,
                                               local_document_url=local_url)

    def fetch_backup(self, document):
        return self.backup.get(document.id)

    def build(self, batch_size=2, rebuild=False, client=None):
        return pz.build_major_zips(self.project, self.admission_round, self.major, self.pud,
                                   client or self.client_s3, 'portfolio-bucket', batch_size,
                                   rebuild=rebuild, fetch_backup=self.fetch_backup,
                                   log=lambda *args: None)

    def open_zip(self, key):
        return zipfile.ZipFile(io.BytesIO(self.client_s3.objects[key]))

    def read_index(self, zf):
        text = zf.read('index.csv').decode('utf-8-sig')
        return list(csv.DictReader(io.StringIO(text)))

    # -- tests --

    def test_paid_applicants_sorted_by_name(self):
        self.make_applicant('1000000000003', 'ค', 'ก')
        self.make_applicant('1000000000001', 'ก', 'ข')
        self.make_applicant('1000000000002', 'ข', 'ก', paid=False)
        self.make_applicant('1000000000004', 'ก', 'ก')
        self.make_applicant('1000000000005', 'ก', 'ก', major=self.other_major)

        applicants = pz.load_paid_applicants_by_name(self.project, self.admission_round,
                                                     self.major)
        self.assertEqual([a.national_id for a in applicants],
                         ['1000000000004', '1000000000001', '1000000000003'])

    def test_build_zips_contents_and_rows(self):
        from backoffice.models import PortfolioZipFile

        a1 = self.make_applicant('1000000000001', 'กมล', 'ใจดี')
        a2 = self.make_applicant('1000000000002', 'ขจร', 'สุขใจ')
        a3 = self.make_applicant('1000000000003', 'คมสัน', 'ดีมาก')
        a4 = self.make_applicant('1000000000004', 'งาม', 'ตา')
        self.make_applicant('1000000000005', 'จันทร์', 'เพ็ญ')
        self.make_applicant('1000000000006', 'ฉัตร', 'ชัย', paid=False)

        self.add_file(a1, 'one.pdf', b'local-1', rank=0)
        self.add_file(a1, 'two.PDF', b'backup-1', rank=1, on_disk=False)
        self.add_link(a2, 'https://folio.mytcas.com/_/abc', 'm-abc.pdf', b'mirror-2')
        self.add_link(a3, 'https://folio.mytcas.com/_/def', 'm-def.pdf', None)
        self.add_link(a3, 'https://example.org/not-mirrored', rank=1)
        self.add_file(a4, 'gone.pdf', b'', on_disk=False)
        del self.backup[a4.uploadeddocument_set.get().id]
        # a5 uploads nothing

        summary = self.build(batch_size=2)

        rows = list(PortfolioZipFile.objects.order_by('batch_number'))
        self.assertEqual(len(rows), 3)
        self.assertEqual(summary['batches'], 3)
        self.assertEqual(summary['applicant_count'], 5)
        self.assertEqual(summary['file_count'], 3)
        self.assertEqual(summary['missing_count'], 3)
        self.assertEqual(summary['status_counts'],
                         {'local': 1, 'backup': 1, 'mirror': 1, 'mirror-missing': 1,
                          'url-only': 1, 'missing': 1, 'no-upload': 1})

        r1 = rows[0]
        self.assertEqual((r1.first_seq, r1.last_seq, r1.applicant_count), (1, 2, 2))
        self.assertEqual((r1.file_count, r1.missing_count), (3, 0))
        self.assertEqual(r1.first_applicant_name, 'กมล ใจดี')
        self.assertEqual(r1.last_applicant_name, 'ขจร สุขใจ')
        self.assertEqual(r1.bucket_name, 'portfolio-bucket')
        self.assertRegex(r1.object_key,
                         rf'^{self.project.id}/{self.admission_round.id}/major-007/'
                         r'\d{8}-\d{6}/batch-01\.zip$')
        self.assertEqual(r1.size, len(self.client_s3.objects[r1.object_key]))
        self.assertEqual(r1.expires_at - r1.built_at, timedelta(days=30))
        self.assertEqual([(r.first_seq, r.last_seq, r.missing_count) for r in rows[1:]],
                         [(3, 4, 2), (5, 5, 1)])

        with self.open_zip(r1.object_key) as zf:
            self.assertEqual(zf.namelist(), ['001_1000000000001_กมล_ใจดี.pdf',
                                             '001_1000000000001_กมล_ใจดี_2.pdf',
                                             '002_1000000000002_ขจร_สุขใจ.pdf',
                                             'index.csv'])
            self.assertEqual(zf.read('001_1000000000001_กมล_ใจดี.pdf'), b'local-1')
            self.assertEqual(zf.read('001_1000000000001_กมล_ใจดี_2.pdf'), b'backup-1')
            self.assertEqual(zf.read('002_1000000000002_ขจร_สุขใจ.pdf'), b'mirror-2')
            self.assertIsNone(zf.testzip())
            for info in zf.infolist():
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertTrue((info.external_attr >> 16) & 0o400, info.filename)
            index = self.read_index(zf)
        self.assertEqual([(r['seq'], r['zip_filename'], r['original_filename'], r['status'])
                          for r in index],
                         [('1', '001_1000000000001_กมล_ใจดี.pdf', 'orig-one.pdf', 'local'),
                          ('1', '001_1000000000001_กมล_ใจดี_2.pdf', 'orig-two.PDF', 'backup'),
                          ('2', '002_1000000000002_ขจร_สุขใจ.pdf', '', 'mirror')])
        self.assertEqual(index[2]['document_url'], 'https://folio.mytcas.com/_/abc')

        with self.open_zip(rows[1].object_key) as zf:
            self.assertEqual(zf.namelist(), ['index.csv'])
            index = self.read_index(zf)
        self.assertEqual([(r['seq'], r['zip_filename'], r['status']) for r in index],
                         [('3', '', 'mirror-missing'), ('3', '', 'url-only'),
                          ('4', '', 'missing')])

        with self.open_zip(rows[2].object_key) as zf:
            index = self.read_index(zf)
        self.assertEqual([(r['seq'], r['first_name'], r['status']) for r in index],
                         [('5', 'จันทร์', 'no-upload')])

        self.assertEqual([r['status'] for r in summary['missing_rows']],
                         ['mirror-missing', 'url-only', 'missing', 'no-upload'])

    def test_second_run_skips_and_rebuild_replaces(self):
        from backoffice.models import PortfolioZipFile

        a = self.make_applicant('1000000000001', 'กมล', 'ใจดี')
        self.add_file(a, 'one.pdf', b'v1')
        self.build()
        old_key = PortfolioZipFile.objects.get().object_key

        self.assertEqual(self.build(), {'skipped': True})
        self.assertEqual(PortfolioZipFile.objects.get().object_key, old_key)

        # a different timestamp in the key, even within the same second
        from unittest import mock
        later = datetime.now() + timedelta(seconds=5)
        with mock.patch.object(pz, 'datetime', wraps=datetime) as mocked:
            mocked.now.return_value = later
            summary = self.build(rebuild=True)
        self.assertFalse(summary['skipped'])
        new_key = PortfolioZipFile.objects.get().object_key
        self.assertNotEqual(new_key, old_key)
        self.assertEqual(self.client_s3.deleted, [old_key])
        self.assertIn(new_key, self.client_s3.objects)

    def test_failure_deletes_uploads_and_keeps_old_rows(self):
        from backoffice.models import PortfolioZipFile

        for i in range(3):
            a = self.make_applicant(f'100000000000{i}', f'ชื่อ{i}', 'สกุล')
            self.add_file(a, f'f{i}.pdf', b'data')

        failing = FakeS3(fail_on_complete=2)
        with self.assertRaises(RuntimeError):
            self.build(batch_size=2, client=failing)
        self.assertEqual(PortfolioZipFile.objects.count(), 0)
        self.assertEqual(failing.objects, {})
        self.assertEqual(len(failing.deleted), 1)
        self.assertEqual(len(failing.aborted), 1)

    def test_no_paid_applicants(self):
        from backoffice.models import PortfolioZipFile

        self.make_applicant('1000000000001', 'กมล', 'ใจดี', paid=False)
        summary = self.build()
        self.assertEqual(summary['batches'], 0)
        self.assertEqual(PortfolioZipFile.objects.count(), 0)
        self.assertEqual(self.client_s3.objects, {})

    def test_find_project_uploaded_document(self):
        from appl.models import ProjectUploadedDocument

        self.assertEqual(pz.find_project_uploaded_document(self.project, 'portfolio'),
                         self.pud)
        with self.assertRaises(ValueError):
            pz.find_project_uploaded_document(self.project, 'nope')
        ProjectUploadedDocument.objects.create(
            rank=2, title='Common', descriptions='', specifications='',
            allowed_extentions='pdf', document_key='portfolio', is_common_document=True)
        with self.assertRaises(ValueError):
            pz.find_project_uploaded_document(self.project, 'portfolio')

    def test_plan_major_for_dry_run(self):
        a = self.make_applicant('1000000000001', 'กมล', 'ใจดี')
        self.add_file(a, 'one.pdf', b'x')
        self.add_file(a, 'two.pdf', b'y', on_disk=False)
        self.make_applicant('1000000000002', 'ขจร', 'สุขใจ')

        applicants = pz.load_paid_applicants_by_name(self.project, self.admission_round,
                                                     self.major)
        plan = pz.plan_major(applicants,
                             pz.load_documents_by_applicant(applicants, self.pud), 1)
        self.assertEqual([[(seq, files) for seq, _, files in batch] for batch in plan], [
            [(1, [('001_1000000000001_กมล_ใจดี.pdf', 'local'),
                  ('001_1000000000001_กมล_ใจดี_2.pdf', 'backup')])],
            [(2, [('', 'no-upload')])],
        ])
