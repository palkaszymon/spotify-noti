import json
import base64
from requests import get, post
from os import getenv

client_id = getenv('CLIENT_ID')
client_secret = getenv('CLIENT_SECRET')

playlist_ids = ['6jb23MIDO80GqVaNIsyUfO', '4wWGESRiQIVhFrabk4RwJA', '5037GRVTAdYiQvGRpzWIDT', '7ep8g0ewFtEKjhgwmFy957']

def lambda_handler(event, context):
    msg = ''
    params = event.get('queryStringParameters')
    mode = params.get('mode')
    if mode == 'dupa':
        msg = Playlist('37i9dQZF1DWY7IeIP1cdjF').get_playlist_items()
    elif mode == "elko":
        msg = 'elko'
    return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"{msg}",
        }),
        }

def get_oauth_token():
    auth_string = client_id + ':' + client_secret
    auth_b64 = str(base64.b64encode(auth_string.encode('UTF-8')), 'UTF-8')
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        "Authorization": "Basic " + auth_b64,
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    result = post(url, headers=headers, data=data)
    return json.loads(result.content)['access_token']

class Share():
    def get_response_data(self):
        url = f"https://api.spotify.com/v1/playlists/{self.id}?market=PL"
        response = get(url, data=None, headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_oauth_token()}"
        })
        return response.json()

    def get_track_name(self, id):
        return str([item['track']['name']for item in self.response['tracks']['items']if item['track']['id'] == id][0])

    def get_artist_list(self, track_id):
        return [item['track']['artists'][i]['name'] for item in self.response['tracks']['items'] for i in range(len(item['track']['artists'])) if item['track']['id'] == track_id]  

class Playlist(Share):  
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data()

    def get_playlist_name(self):
        return self.response['name']

    def get_playlist_items(self):
        id_list = [item['track']['id'] for item in self.response['tracks']['items']]
        return id_list

    def playlist_new_songs(self):
        old_list = json.load()
        new_list = self.get_playlist_items()
        return [song for song in new_list if song not in old_list]

    def save_playlist_songs(self):
        # will be database (maybe neo4j) for now in file
        pass