from requests import get, post
import json
from base64 import b64encode
from utils.AwsFunctions import get_secret
from datetime import datetime, date
from collections import OrderedDict
from tenacity import retry, stop_after_attempt

SPOTIFY_CREDS = get_secret('spotify-api-creds')
client_id, client_secret = SPOTIFY_CREDS['CLIENT_ID'], SPOTIFY_CREDS['CLIENT_SECRET']

def get_oauth_token():
    auth_string = client_id + ':' + client_secret
    auth_b64 = str(b64encode(auth_string.encode('UTF-8')), 'UTF-8')
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        "Authorization": "Basic " + auth_b64,
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    return json.loads(result.content)['access_token']

oauth = get_oauth_token()

class Share():
    @retry(stop=stop_after_attempt(3))
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data()

    def get_response_data(self):
        mode = type(self)
        if mode == Playlist:
            url = f"https://api.spotify.com/v1/playlists/{self.id}?market=PL"
        elif mode == Artist:
            url = f"https://api.spotify.com/v1/artists/{self.id}/albums?include_groups=album%2Csingle&market=PL"
        response = get(url, data=None, headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {oauth}"
        }).json()
        return response
    
class Playlist(Share):
    def get_artist_list(self, track_id):
        return [{'artist_name': item['track']['artists'][i]['name'], 'artist_id': item['track']['artists'][i]['id']} for item in self.response['tracks']['items'] for i in range(len(item['track']['artists'])) if item['track']['id'] == track_id]

    def get_playlist_name(self):
        return self.response['name']

    def get_final_items(self):
        track_list = [{'id': item['track']['id'], 'name': item['track']['name'], 'artists': self.get_artist_list(item['track']['id'])} for item in self.response['tracks']['items']]
        return track_list
    
    def create_item(self, tx, track):
        result = tx.run(
"""
MERGE (p:Playlist {playlist_id: $playlist_id})
MERGE (t:Track {name: $name, id: $id})
WITH $artist_list as x
UNWIND x as l
MERGE (a:Artist {artist_name: l.artist_name, artist_id: l.artist_id})
WITH l
MATCH (a:Artist {artist_id: l.artist_id}), (t:Track {id: $id}), (p:Playlist {playlist_id: $playlist_id})
MERGE (t)-[:SONG_OF]->(a)
MERGE (t)-[:APPEARS_ON]->(p)
""",
    id=track['id'], name=track['name'], artist_list=track['artists'], playlist_id=self.id
    )
        summary = result.consume()
        return result, summary
    
    @staticmethod
    def get_id_list(tx):
        result = tx.run(
"""
MATCH (p:Playlist)
RETURN p.playlist_id
""")
        return [record.value() for record in result]
    
class Artist(Share):
    def get_artist_list(self, track_id):
        return [{'artist_name': item['artists'][i]['name'], 'artist_id': item['artists'][i]['id']} for item in self.response['items'] for i in range(len(item['artists'])) if item['id'] == track_id]
    
    def get_items(self):
        try:
            return [{'id': item['id'], 'name': item['name'], 'type': item['album_type'], 'artists': self.get_artist_list(item['id']), 'release_date': item['release_date']} for item in self.response['items']]
        except KeyError:
            print(self.response, self.id)
            
    # Sorts the albums by release date descending, and returns the newest 3
    def get_final_items(self):
        albums = sorted(self.get_items(), key = lambda x: datetime.strptime(self.check_date(x['release_date']), '%Y-%m-%d'), reverse=True)
        if len(albums) != 2:
            filter_dupes =  [albums[i] for i in range(len(albums)-1) if albums[i]['name'] != albums[i+1]['name']][:3]
        else:
            if albums[0]['name'] != albums[1]['name']:
                filter_dupes = albums[:2]
            else:
                filter_dupes = albums[:1]
        return filter_dupes

    @staticmethod
    def create_item(tx, album):
        result = tx.run(
"""
MERGE (al:Album {name: $name, type: $type, release_date: $release_date, id: $id})
WITH $artist_list as x
UNWIND x as l
MERGE (a:Artist {artist_name: l.artist_name, artist_id: l.artist_id})
WITH l
MATCH (a:Artist {artist_id: l.artist_id}), (al:Album {id: $id})
MERGE (al)-[:ALBUM_OF]->(a)
""",
    name=album['name'], type=album['type'], release_date= album['release_date'], id=album['id'], artist_list=album['artists']
    )
        summary = result.consume()
        return result, summary
    
    @staticmethod
    def delete_oldest(tx, album):
        result = tx.run(
"""
MATCH (al:Album)--(a:Artist {artist_id: $artist_id})
WITH min(al.release_date) as min
MATCH (al:Album) WHERE al.release_date = min
DETACH DELETE al
""",
    artist_id=album['artists'][0]['artist_id']
    )
        return result
    
    @staticmethod
    def get_id_list(tx):
        result = tx.run(
"""
MATCH (a:Artist)<-[:FOLLOWS]-(User)
with distinct a, a.check as check
set a.check=True
return a.artist_id, check
""")
        return [record.data() for record in result]
    
    def get_artist_users(tx, artist_id):
        result = tx.run(
"""
MATCH (a:Artist {artist_id: $artist_id})<--(u:User)
RETURN
"""
        )
        return result
    
    @staticmethod
    def get_artist_emails(tx, albumlist):
        artist_ids = list(OrderedDict.fromkeys([album['artists'][0]['artist_id'] for album in albumlist]))
        result = tx.run(
"""
MATCH (u:User)-[:FOLLOWS]->(a:Artist) where a.artist_id in $artist_ids
RETURN a.artist_id as artist_id, collect(u.email) as emails
""",
    artist_ids = artist_ids
)
        emails = [record.data() for record in result]
        return emails

    @staticmethod
    def check_date(date_text):
        check_date = None
        try:
            date.fromisoformat(date_text)
            check_date = date_text
        except ValueError:
            if len(date_text) == 4:
                check_date = f"{date_text}-01-01"
        return check_date
