import json
import base64
from requests import get, post
from neo4j import GraphDatabase
import boto3
from botocore.exceptions import ClientError
import datetime

def get_secret(secret_name):
    region_name = "eu-central-1"
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
    return json.loads(get_secret_value_response['SecretString'])

SPOTIFY_CREDS, NEO4J_CREDS = get_secret('spotify-api-creds'), get_secret('neo4j-creds')
client_id, client_secret = SPOTIFY_CREDS['CLIENT_ID'], SPOTIFY_CREDS['CLIENT_SECRET']
uri, user, password = NEO4J_CREDS['NEO4J_URI'], NEO4J_CREDS['NEO4J_USERNAME'], NEO4J_CREDS['NEO4J_PASSWORD']

def lambda_handler(event, context):
    artist_ids = ['1URnnhqYAYcrqrcwql10ft', '20qISvAhX20dpIbOOzGK3q', '7EQ0qTo7fWT7DPxmxtSYEc', '496nklFjflGjJOhhfhH2Nc']
    msg = ''
    params = event.get('queryStringParameters')
    mode = params.get('mode')
    if mode == '1':
        msg = '1'
        new = []
        Artist.neo_write(artist_ids, firstrun=True)
        # lnvoke_lam = boto3.client("lambda", region_name='eu-central-1')
        # payload = {'message': 'Siema eniu'}
        # response = lnvoke_lam.invoke(FunctionName="arn:aws:lambda:eu-central-1:529336170453:function:sam-app-SendEmailFunction-3UgqZ4QN5w68",
        # InvocationType="Event", Payload=json.dumps(payload))
    elif mode == "2":
        msg = '2'
    return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"{msg}"
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

    def get_response_data(self, type):
        if type == 'playlist':
            url = f"https://api.spotify.com/v1/playlists/{self.id}?market=PL"
        elif type == 'artist':
            url = f"https://api.spotify.com/v1/artists/{self.id}/albums?include_groups=album%2Csingle&market=PL"
        response = get(url, data=None, headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_oauth_token()}"
        })
        return response.json()

class Playlist(Share):   
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data('playlist')

    def get_artist_list(self, track_id):
        return [{'artist_name': item['track']['artists'][i]['name'], 'artist_id': item['track']['artists'][i]['id']} for item in self.response['tracks']['items'] for i in range(len(item['track']['artists'])) if item['track']['id'] == track_id]

    def get_playlist_name(self):
        return self.response['name']

    def get_items(self):
        track_list = [{'track_id': item['track']['id'], 'track_name': item['track']['name'], 'artists': self.get_artist_list(item['track']['id'])} for item in self.response['tracks']['items']]
        return track_list

    def create_track(self, tx, track):
        result = tx.run(
"""
MERGE (p:Playlist {playlist_id: $playlist_id})
MERGE (t:Track {track_name: $track_name, track_id: $track_id})
WITH $artist_list as x
UNWIND x as l
MERGE (a:Artist {artist_name: l.artist_name, artist_id: l.artist_id})
WITH l
MATCH (a:Artist {artist_id: l.artist_id}), (t:Track {track_id: $track_id}), (p:Playlist {playlist_id: $playlist_id})
MERGE (t)-[:SONG_OF]->(a)
MERGE (t)-[:APPEARS_ON]->(p)
""",
    track_id=track['track_id'], track_name=track['track_name'], artist_list=track['artists'], playlist_id=self.id
    )
        summary = result.consume()
        return result, summary

class Artist(Share):
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data('artist')
    
    def get_artist_list(self, track_id):
        return [{'artist_name': item['artists'][i]['name'], 'artist_id': item['artists'][i]['id']} for item in self.response['items'] for i in range(len(item['artists'])) if item['id'] == track_id]
    
    def get_items(self):
        return [{'album_id': item['id'], 'album_name': item['name'], 'album_type': item['album_type'], 'artists': self.get_artist_list(item['id']), 'release_date': item['release_date']} for item in self.response['items']]
    
    def get_filtered_albums(self):
        albums = sorted(self.get_items(), key = lambda x: datetime.datetime.strptime(x['release_date'], '%Y-%m-%d'), reverse=True)
        return [albums[i] for i in range(len(albums)-1) if albums[i]['album_name'] != albums[i+1]['album_name']][:3]
    
    def create_album(self, tx, album):
        result = tx.run(
"""
MERGE (al:Album {album_name: $album_name, album_type: $album_type, release_date: $release_date, album_id: $album_id})
WITH $artist_list as x
UNWIND x as l
MERGE (a:Artist {artist_name: l.artist_name, artist_id: l.artist_id})
WITH l
MATCH (a:Artist {artist_id: l.artist_id}), (al:Album {album_id: $album_id})
MERGE (al)-[:ALBUM_OF]->(a)
""",
    album_name=album['album_name'], album_type=album['album_type'], release_date= album['release_date'], album_id=album['album_id'], artist_list=album['artists']
    )
        summary = result.consume()
        return result, summary
    
    def delete_oldest(self, tx, album):
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
    
    def neo_write(artist_ids, firstrun=False):
        new = []
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                    with driver.session() as session:
                        for id in artist_ids:
                            current = Artist(id)
                            for album in current.get_filtered_albums():
                                try:
                                    print(album)
                                    tx = session.execute_write(current.create_album, album)
                                    if firstrun == False:
                                        check = tx[1].counters.nodes_created
                                        if check != 0:
                                            new.append(album)
                                            session.execute_write(current.delete_oldest, album)
                                            print(f"Album {album['album_name']} write success!")
                                        else:
                                            print(f"Album {album['album_name']} already exists!")
                                except Exception as e:
                                    print(e)