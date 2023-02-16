import json
import base64
from requests import get, post
from os import getenv
from neo4j import GraphDatabase
import time

client_id= ''
client_secret= ''
uri = ''
user = ''
password = ''

playlist_ids = ['37i9dQZF1DWY7IeIP1cdjF', '37i9dQZF1DWX5ZOsG2Ogi1', '37i9dQZF1EQmg9rwHdCwFW', '37i9dQZF1DX10zKzsJ2jva']

def lambda_handler(event, context):
    msg = ''
    times = []
    params = event.get('queryStringParameters')
    mode = params.get('mode')
    if mode == '1':
        msg = '1'
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        with driver.session() as session:
            for playlist in playlist_ids:
                current_playlist = Playlist(playlist)
                st = time.time()
                print(current_playlist.get_playlist_items())
                for track in current_playlist.get_playlist_items():
                    try:
                        session.execute_write(current_playlist.create_track, track)
                        print(f"Track {track['track_name']} write success!")
                    except Exception as e:
                        print(e)
                et = time.time()
                times.append(et-st)
            session.close()
            driver.close()
    elif mode == "2":
        msg = '2'
    return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"{msg}, {times}"
        }),
        }

class Share():
    def get_oauth_token(self):
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

    def get_response_data(self):
        url = f"https://api.spotify.com/v1/playlists/{self.id}?market=PL"
        response = get(url, data=None, headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_oauth_token()}"
        })
        return response.json()

    def get_track_name(self, id):
        return str([item['track']['name']for item in self.response['tracks']['items']if item['track']['id'] == id][0])

    def get_artist_list(self, track_id):
        return [{'artist_name': item['track']['artists'][i]['name'], 'artist_id': item['track']['artists'][i]['id']} for item in self.response['tracks']['items'] for i in range(len(item['track']['artists'])) if item['track']['id'] == track_id]  

class Playlist(Share):   
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data()

    def get_playlist_name(self):
        return self.response['name']

    def get_playlist_items(self):
        track_list = [{'track_id': item['track']['id'], 'track_name': item['track']['name'], 'artists': self.get_artist_list(item['track']['id'])} for item in self.response['tracks']['items']]
        return track_list

    def playlist_new_songs(self):
        old_list = json.load()
        new_list = self.get_playlist_items()
        return [song for song in new_list if song not in old_list]

    def save_playlist_songs(self):
        # will be database (maybe neo4j) for now in file
        pass
    
    # <----------NEO4J DATABASE FUNCTIONS---------->
    def create_track(self, tx, track):
        result = tx.run(
"""
MERGE (t:Track {track_name: $track_name, track_id: $track_id})
WITH $artist_list as x
UNWIND x as l
MERGE (a:Artist {artist_name: l.artist_name, artist_id: l.artist_id})
WITH l
MATCH (a:Artist {artist_id: l.artist_id}), (t:Track {track_id: $track_id})
MERGE (t)-[:SONG_OF]->(a)
""",
    track_id=track['track_id'], track_name=track['track_name'], artist_list=track['artists']
    )
        return result
