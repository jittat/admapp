import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from botocore.client import Config
import os
from urllib.parse import urlparse, urlunparse
from cryptography.fernet import Fernet

from django_bootstrap import bootstrap
from django.conf import settings

bootstrap()

from appl.models import UploadedDocument, ProjectUploadedDocument

def upload_to_s3(file_path,
                 bucket_name,
                 object_name=None,
                 aws_access_key=None,
                 aws_secret_key=None,
                 endpoint_url=None):
    if object_name is None:
        object_name = os.path.basename(file_path)

    # Basic validations
    if not file_path or not os.path.isfile(file_path):
        print(f"The file {file_path} was not found or is not a regular file.")
        return False
    if not bucket_name:
        print("Bucket name is required")
        return False

    # Initialize S3 client with explicit signature v4 (works for most S3-compatible services)
    s3_config = Config(signature_version='s3v4')
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        endpoint_url=endpoint_url,
        config=s3_config
    )

    try:
        #print(f"Uploading {file_path} -> bucket={bucket_name}, key={object_name}, endpoint={endpoint_url}")
        s3_client.upload_file(file_path, bucket_name, object_name)
        #print(f"File {file_path} uploaded to {bucket_name}/{object_name}")
        return True
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
    except NoCredentialsError:
        print("Credentials not available.")
    except ClientError as e:
        # Print full response if available to aid debugging (status, error message)
        resp = getattr(e, 'response', None)
        print(f"Failed to upload file: {e}. Response: {resp}")
    except Exception as e:
        print(f"Unexpected error while uploading: {type(e).__name__}: {e}")
    return False


def encrypt_document(uploaded_document):
    # Generate a key for encryption
    key = settings.S3_MEDIA_BACKUP_ENCRYPTION_KEY  # Ensure this key is securely stored and retrieved
    cipher = Fernet(key)

    uploaded_file_abspath = os.path.join(settings.MEDIA_ROOT, uploaded_document.uploaded_file.name)

    # Read the content of the uploaded document
    with open(uploaded_file_abspath, 'rb') as file:
        file_data = file.read()

    # Encrypt the file data
    encrypted_data = cipher.encrypt(file_data)

    # Save the encrypted file to /tmp
    encrypted_file_path = f"/tmp/{uploaded_document.id}.enc"
    with open(encrypted_file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)

    return encrypted_file_path

def backup_uploaded_document(uploaded_document, 
                             bucket_name, 
                             aws_access_key, 
                             aws_secret_key, 
                             endpoint_url):

    try:
        encrypted_document_filename = encrypt_document(uploaded_document)
    except:
        encrypted_document_filename = None

    if not encrypted_document_filename:
        print(f"Error encrypting document {uploaded_document.id}, skipping backup.")
        return

    object_name = uploaded_document.encrypted_backup_filename()
    result = upload_to_s3(encrypted_document_filename, 
                          bucket_name, 
                          object_name, 
                          aws_access_key, 
                          aws_secret_key, 
                          endpoint_url)
    if result:
        print(f"Document {uploaded_document.id} backed up to {object_name}.")
    os.remove(encrypted_document_filename)


def main():
    import sys

    project_uploaded_document_id = int(sys.argv[1])
    project_uploaded_document = ProjectUploadedDocument.objects.get(pk=project_uploaded_document_id)

    bucket_name = settings.S3_MEDIA_BACKUP_BUCKET_NAME
    aws_access_key = settings.S3_MEDIA_BACKUP_ACCESS_KEY
    aws_secret_key = settings.S3_MEDIA_BACKUP_SECRET_KEY
    endpoint_url = settings.S3_MEDIA_BACKUP_ENDPOINT

    documents = UploadedDocument.objects.filter(project_uploaded_document=project_uploaded_document)

    print(f'{documents.count()} documents to backup.')

    for u in documents:
        backup_uploaded_document(u, 
                                 bucket_name, 
                                 aws_access_key, 
                                 aws_secret_key, 
                                 endpoint_url)
    
if __name__ == "__main__":
    main()