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

artist_ids = ['1URnnhqYAYcrqrcwql10ft', '20qISvAhX20dpIbOOzGK3q', '7EQ0qTo7fWT7DPxmxtSYEc', '496nklFjflGjJOhhfhH2Nc']
playlist_ids = ['4ul6VwbC9q89M3FAs8fOdb', '5dtDRRVVYQSnBsKNAzlDLo', '5037GRVTAdYiQvGRpzWIDT', '69n8hWNmelZfJymzUL6gAl']

def lambda_handler(event, context):
    msg = ''
    params = event.get('queryStringParameters')
    mode = params.get('mode')
    if mode == 'artist':
        firstrun = eval(params.get('f'))
        msg = 'artist'
        Artist.neo_write(Artist, firstrun)
        # lnvoke_lam = boto3.client("lambda", region_name='eu-central-1')
        # payload = {'message': 'Siema eniu'}
        # response = lnvoke_lam.invoke(FunctionName="arn:aws:lambda:eu-central-1:529336170453:function:sam-app-SendEmailFunction-3UgqZ4QN5w68",
        # InvocationType="Event", Payload=json.dumps(payload))
    elif mode == "playlist":
        msg = 'playlist'
        Artist.neo_write(Playlist)
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
    
    def neo_write(object, firstrun=False):
        new = []
        if object == Playlist:
            id_list = playlist_ids
        else:
            id_list = artist_ids
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                    with driver.session() as session:
                        for id in id_list:
                            current = object(id)
                            for item in current.get_final_items():
                                try:
                                    tx = session.execute_write(current.create_item, item)
                                    if firstrun == False:
                                        check = tx[1].counters.nodes_created
                                        if check != 0:
                                            new.append(item)
                                            if object == Artist:
                                                session.execute_write(current.delete_oldest, item)
                                except Exception as e:
                                    print(e)

class Playlist(Share):   
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data('playlist')

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

class Artist(Share):
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data('artist')
    
    def get_artist_list(self, track_id):
        return [{'artist_name': item['artists'][i]['name'], 'artist_id': item['artists'][i]['id']} for item in self.response['items'] for i in range(len(item['artists'])) if item['id'] == track_id]
    
    def get_items(self):
        return [{'id': item['id'], 'name': item['name'], 'type': item['album_type'], 'artists': self.get_artist_list(item['id']), 'release_date': item['release_date']} for item in self.response['items']]
    
    # Sorts the albums by release date descending, and returns the newest 3
    def get_final_items(self):
        albums = sorted(self.get_items(), key = lambda x: datetime.datetime.strptime(x['release_date'], '%Y-%m-%d'), reverse=True)
        return [albums[i] for i in range(len(albums)-1) if albums[i]['name'] != albums[i+1]['name']][:3]
    
    def create_item(self, tx, album):
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