import base64
import requests
import json
from dotenv import load_dotenv
from os import getenv

load_dotenv()
client_id = getenv('CLIENT_ID')
client_secret = getenv('CLIENT_SECRET')
playlist_ids = ['6jb23MIDO80GqVaNIsyUfO', '4wWGESRiQIVhFrabk4RwJA', '5037GRVTAdYiQvGRpzWIDT', '7ep8g0ewFtEKjhgwmFy957']
class Songlist:  
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data()

    def get_oauth_token(self):
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

    def get_response_data(self):
        url = f"https://api.spotify.com/v1/playlists/{self.id}?market=PL"
        response = requests.get(url, data=None, headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_oauth_token()}"
        })
        return response.json()

    def get_track_name(self, id):
        return [item['track']['name']for item in self.response['tracks']['items']if item['track']['id'] == id][0]

    def get_artist_list(self, track_id):
        return [item['track']['artists'][i]['name'] for item in self.response['tracks']['items'] for i in range(len(item['track']['artists'])) if item['track']['id'] == track_id]

    def get_playlist_name(self):
        return self.response['name']

    def get_playlist_items(self):
        id_list = [item['track']['id'] for item in self.response['tracks']['items']]
        with open('list.json', 'w') as f:
            json.dump(id_list, f)
        return id_list

    def playlist_new_songs(self):
        with open(f'playlists/{self.id}.json', 'r') as f:
            old_list = json.load(f)
            new_list = self.get_playlist_items()
        return [song for song in new_list if song not in old_list]

    def save_playlist_songs(self):
        # will be database (maybe neo4j) for now in file
        with open(f'playlists/{self.id}.json', 'w') as f:
            json.dump(self.get_playlist_items(), f)

# final_dict = {}
# for id in playlist_ids:
#     new_songs = []
#     obj = Songlist(id)
#     for song in obj.playlist_new_songs():
#         temp = ', '
#         new_songs.append([obj.get_track_name(song), temp.join(obj.get_artist_list(song))])
#     final_dict[obj.get_playlist_name()] = new_songs
# print(final_dict)

for id in playlist_ids:
    print(Songlist(id).playlist_new_songs())