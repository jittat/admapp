import suds
import json

from django.conf import settings

def create_cupt_client():
    url = getattr(settings,'CUPT_SERVICE_URL','')
    
    if url == '':
        return None

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

