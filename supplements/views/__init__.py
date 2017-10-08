from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from regis.decorators import appl_login_required
from appl.models import AdmissionProject, AdmissionRound
from supplements.models import ProjectSupplement, ProjectSupplementConfig

from supplements.models import PROJECT_SUPPLEMENTS
from supplements.models import load_project_supplements

def get_function(fname):
    import importlib
    mod_name, func_name = fname.rsplit('.',1)
    mod = importlib.import_module(mod_name)
    f = getattr(mod, func_name)
    return f

@appl_login_required
def index(request, project_id, round_id):
    applicant = request.applicant
    admission_project = get_object_or_404(AdmissionProject,
                                          pk=project_id)
    admission_round = get_object_or_404(AdmissionRound,
                                        pk=round_id)
    
    supplement_configs = PROJECT_SUPPLEMENTS[admission_project.title]
    supplements = load_project_supplements(applicant,
                                           admission_project,
                                           supplement_configs)

    if request.method == 'POST':
        if 'ok' not in request.POST:
            return redirect(reverse('appl:index'))
            
        has_error = False
        new_data = {}
        for config in supplement_configs:
            instance = supplements[config.name]
            if instance:
                data = instance.get_data()
            else:
                data = {}
            
            fname = config.form_processing_function
            if fname != '':
                f = get_function(fname)
                form_result = f(request,
                                applicant,
                                admission_project,
                                admission_round,
                                config.form_prefix,
                                data)
                if not form_result[0]:
                    has_error = True
                else:
                    new_data[config.name] = form_result[1]
                    
        if not has_error:
            for config in supplement_configs:
                instance = supplements[config.name]
                if not instance:
                    instance = ProjectSupplement(applicant=applicant,
                                                 admission_project=admission_project,
                                                 name=config.name)
                instance.set_data(new_data[config.name])
                instance.save()
            return redirect(reverse('appl:index'))

    context = { 'applicant': applicant,
                'admission_project': admission_project,
                'admission_round': admission_round,
                'configs': supplement_configs }
        
    supplement_contexts = {}
    for config in supplement_configs:
        instance = supplements[config.name]
        if instance:
            data = instance.get_data()
        else:
            data = {}
            
        fname = config.form_init_function
        if fname != '':
            f = get_function(fname)
            sup_context = f(request,
                            applicant,
                            admission_project,
                            admission_round,
                            config.form_prefix,
                            data)
        else:
            sup_context = {}
        supplement_contexts[config.name] = sup_context

    context.update(supplement_contexts)
        
    return render(request,
                  'supplements/index.html',
                  context)
