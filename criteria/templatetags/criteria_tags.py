import json

from django import template
from django.utils.safestring import mark_safe

from criteria.criteria_options import CRITERIA_OPTIONS, PORTFOLIO_SCORING_TAGS

register = template.Library()

EXCLUDED_TAGS = [
    {
        'conditions': {
            'project_ids': [1,2,3,4,8,9,32,33],
        },
        'excluded_tags': [
            'GPAX_5_SEMESTER',
            'GPAX'
        ]
    },
    {
        'conditions': {
            'project_ids': [101],
        },
        'excluded_tags': [
            'GPAX_4_SEMESTER',
            'GPAX'
        ]
    },
    {
        'conditions': {
            'project_ids': [11,12,13,14,16,17,18,23,24,34,35,36],
        },
        'excluded_tags': [
            'GPAX_4_SEMESTER',
            'GPAX',
        ]
    },
    {
        'conditions': {
            'project_ids': [28],
        },
        'excluded_tags': [
            'GPAX_4_SEMESTER',
            'GPAX_5_SEMESTER',
        ]
    },
]

def exclude_tags(options, admission_project):
    if admission_project == None:
        return options

    removed_tags = []
    for tag_item in EXCLUDED_TAGS:
        if 'conditions' in tag_item:
            is_passed = True
            for c in tag_item['conditions']:
                if c == 'project_ids':
                    if admission_project.id not in tag_item['conditions']['project_ids']:
                        is_passed = False

            if is_passed:
                removed_tags += tag_item['excluded_tags']

    if removed_tags == []:
        return options

    import copy
    updated_options = copy.deepcopy(options)
    updated_options['general_required_tags'] = [tag for tag in options['general_required_tags']
                                                if tag['score_type'] not in removed_tags]
    updated_options['general_scoring_tags'] = [tag for tag in options['general_scoring_tags']
                                               if tag['score_type'] not in removed_tags]
    updated_options['test_tags'] = [tag for tag in options['test_tags']
                                    if tag['score_type'] not in removed_tags]

    return updated_options
    
def get_round_scoring_extra_tags(admission_round):
    if admission_round is None or not admission_round.is_portfolio_round():
        return [], []
    return (PORTFOLIO_SCORING_TAGS.get('prepend', []),
            PORTFOLIO_SCORING_TAGS.get('append', []))


@register.simple_tag
def criteria_options_as_js(admission_project=None, admission_round=None):
    items = []
    criteria_options = exclude_tags(CRITERIA_OPTIONS, admission_project)
    for cname in criteria_options:
        items.append(f'const {cname} = ' +
                     json.dumps(criteria_options[cname]))

    prepend_tags, append_tags = get_round_scoring_extra_tags(admission_round)
    items.append('const portfolio_scoring_prepend_tags = ' + json.dumps(prepend_tags))
    items.append('const portfolio_scoring_append_tags = ' + json.dumps(append_tags))

    return mark_safe('\n'.join(items))
