import json
import ssl

import json

import suds
import requests
from django.conf import settings

def cupt_check_status(national_id, first_name, last_name):
    url = getattr(settings,'CUPT_SERVICE_URL','')
    secret_key = getattr(settings,'CUPT_SECRET_KEY','')

    headers = {'secretKey': secret_key}
    data = {
        'citizen_id': national_id,
        'first_name': first_name,
        'last_name': last_name,
    }

    r = requests.get(url, headers=headers, params=data)
    result = {}
    messages = ''
    try:
        result = json.loads(r.text)
        messages = r.text
    except:
        pass

    return result, messages
    

def create_cupt_client():
    url = getattr(settings,'CUPT_SERVICE_URL','')
    
    if url == '':
        return None


    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context
        
    client = suds.Client(url)
    return client


def get_token(client):
    username = getattr(settings,'CUPT_USERNAME','')
    password = getattr(settings,'CUPT_PASSWORD','')
    
    json_str = client.service.service_authen(username,
                                             password)

    try:
        data = json.loads(json_str)
        return data['token']
    except:
        return None


def check_permission(client, token, national_id):
    json_str = client.service.query_data(token,national_id)

    try:
        data = json.loads(json_str)
    except:
        return (False, 'json-error')

    if 'error' in data:
        if 'token' in data['error']:
            return (False, 'token-expired')
        elif 'ID' in data['error']:
            return (False, 'id-not-valid')
        else:
            return (False, 'error-unknown')

    elif 'student_info' in data:
        info = data['student_info']
        if len(info) == 0:
            return (True, '0')
        else:
            return (True, info[0]['STATUS'])
    else:
        return (False, 'error-unknown')

