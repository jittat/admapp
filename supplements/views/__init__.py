from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.urls import reverse

from appl.models import AdmissionProject, AdmissionRound
from regis.decorators import appl_login_required
from supplements.models import PROJECT_SUPPLEMENTS
from supplements.models import ProjectSupplement
from supplements.models import load_project_supplements
from regis.models import LogItem
from .utils import get_function


def render_supplement_block(request,
                            applicant,
                            admission_project,
                            admission_round,
                            block_config):
    loader = get_function(block_config.context_init_function)

    block_context = loader(applicant,
                           admission_project,
                           admission_round)
    
    from django.template.loader import get_template

    template = get_template(block_config.template_name)
    
    html = template.render({ 'applicant': applicant,
                             'admission_project': admission_project,
                             'admission_round': admission_round,
                             'block_config': block_config,
                             'block_context': block_context, })
    return html


def render_supplement_for_backoffice(supplement_config, supplement):
    from django.template.loader import get_template

    template = get_template(supplement_config.backoffice_template)
    try:
        data = supplement.get_data()
    except:
        data = None
        
    html = template.render({ 'instance': data })

    return html


def process_supplement_forms(request,
                             applicant, admission_project, admission_round,
                             supplements, supplement_configs):
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
        return True
    else:
        return False

    
@appl_login_required
def index(request, project_id, round_id):
    applicant = request.applicant
    admission_project = get_object_or_404(AdmissionProject,
                                          pk=project_id)
    admission_round = get_object_or_404(AdmissionRound,
                                        pk=round_id)
    
    project_round = admission_project.get_project_round_for(admission_round)
    is_deadline_passed = project_round.is_deadline_passed()
    
    supplement_configs = PROJECT_SUPPLEMENTS[admission_project.short_title]
    supplements = load_project_supplements(applicant,
                                           admission_project,
                                           supplement_configs)

    if request.method == 'POST':
        if 'ok' not in request.POST:
            return redirect(reverse('appl:index'))
        
        if is_deadline_passed:
            return HttpResponseForbidden()

        result = process_supplement_forms(request,
                                          applicant,
                                          admission_project,
                                          admission_round,
                                          supplements,
                                          supplement_configs)

        LogItem.create('Saved supplements for project %d' % admission_project.id,
                       applicant, request)

        if result:
            return redirect(reverse('appl:index'))
        

    context = { 'applicant': applicant,
                'admission_project': admission_project,
                'admission_round': admission_round,
                'configs': supplement_configs,
                'is_deadline_passed': is_deadline_passed }

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
