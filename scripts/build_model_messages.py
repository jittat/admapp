from django_bootstrap import bootstrap
bootstrap()

from appl.models import Campus, Faculty, AdmissionProject, AdmissionRound

def dump_data(objects, varname, fields):
    items = []
    for o in objects:
        for f in fields:
            if f != '*':
                items.append(getattr(o,f))
            else:
                items.append(o)

    print(varname,'= [')
    for i in items:
        print("    _('{0}'),".format(i))
    print(']')


def dump_model_data(model,varname,fields):
    objects = model.objects.all()
    dump_data(objects, varname, fields)
    

def dump_header():
    print('from django.utils.translation import ugettext_lazy as _')

    
def main():
    dump_header()
    # noinspection PyTypeChecker
    dump_model_data(Campus, 'CAMPUSES', ['title'])
    dump_model_data(Faculty, 'FACULTIES', ['title'])

    project = AdmissionProject.objects.get(pk=1)
    dump_data(project.major_set.all(), 'MAJORS', ['title'])

    dump_data([project], 'PROJECTS', ['title'])

    dump_data([str(r) for r in AdmissionRound.objects.all()], 'ADMROUNDS', ['*'])
    
if __name__ == '__main__':
    main()
