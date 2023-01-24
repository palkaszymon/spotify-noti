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

def get_api_response():
    url = "https://api.spotify.com/v1/playlists/4ul6VwbC9q89M3FAs8fOdb/tracks?market=PL"
    response = requests.get(url, data=None, headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_oauth_token()}"
    })
    return response.json()

def get_track_name(id):
    response = get_api_response()
    return str([item['track']['name']for item in response['items']if item['track']['id'] == id])

def get_playlist_items():
    response = get_api_response()
    id_list = [item['track']['id'] for item in response['items']]
    track_list = [item['track']['name'] for id in id_list for item in response['items']if item['track']['id'] == id]
    artist_list = []
    for item in response['items']:
        temp = []
        for i in range(len(item['track']['artists'])):
            temp.append(item['track']['artists'][i]['name'])
        artist_list.append(temp)
    final_list = zip(track_list, artist_list)
    return id_list

def look_for_new_songs():
    with open('list.json', 'r') as f:
        old_list = json.load(f)
        new_list = get_playlist_items()
    new_songs = [song for song in new_list if song not in old_list]
