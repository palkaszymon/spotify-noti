import json
import base64
from requests import get, post
from neo4j import GraphDatabase
import boto3
from botocore.exceptions import ClientError

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
    playlist_ids = ['6jb23MIDO80GqVaNIsyUfO', '5037GRVTAdYiQvGRpzWIDT']
    msg = ''
    params = event.get('queryStringParameters')
    mode = params.get('mode')
    if mode == '1':
        msg = '1'
        new = []
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            with driver.session() as session:
                for playlist in playlist_ids:
                    current = Playlist(playlist)
                    for track in current.get_playlist_items():
                        try:
                            tx = session.execute_write(current.create_track, track)
                            check = tx[1].counters.nodes_created
                            if check != 0:
                                new.append(track)
                                print(f"Track {track['track_name']} write success!")
                            else:
                                print(f"Track {track['track_name']} already exists!")
                        except Exception as e:
                            print(e)
            lnvoke_lam = boto3.client("lambda", region_name='eu-central-1')
            payload = {'message': 'Siema eniu'}
            response = lnvoke_lam.invoke(FunctionName="arn:aws:lambda:eu-central-1:529336170453:function:sam-app-SendEmailFunction-3UgqZ4QN5w68",
            InvocationType="Event", Payload=json.dumps(payload))
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
    
    def get_tracks(self, tx):
        result = tx.run("""
MATCH (t:Track)-[r:APPEARS_ON]-(p:Playlist {playlist_id: $playlist_id})
return t, r.playlist_id
    """,
playlist_id=self.id
    )

        return [record["t"] for record in result]
