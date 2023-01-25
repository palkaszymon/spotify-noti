import base64
import requests
import json
from dotenv import load_dotenv
from os import getenv

load_dotenv()
client_id = getenv('CLIENT_ID')
client_secret = getenv('CLIENT_SECRET')

def get_oauth_token():
    auth_string = client_id + ':' + client_secret
    auth_b64 = str(base64.b64encode(auth_string.encode('UTF-8')), 'UTF-8')
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        "Authorization": "Basic " + auth_b64,
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    result = requests.post(url, headers=headers, data=data)
    return json.loads(result.content)['access_token']