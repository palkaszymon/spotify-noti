from utils.Classes import Artist, Playlist
from utils.AwsFunctions import get_secret, invoke_email_lambda
import json
from neo4j import GraphDatabase

NEO4J_CREDS = get_secret('neo4j-creds')
uri, user, password = NEO4J_CREDS['NEO4J_URI'], NEO4J_CREDS['NEO4J_USERNAME'], NEO4J_CREDS['NEO4J_PASSWORD']
driver = GraphDatabase.driver(uri, auth=(user, password))

playlist_ids = ['4ul6VwbC9q89M3FAs8fOdb', '5dtDRRVVYQSnBsKNAzlDLo', '5037GRVTAdYiQvGRpzWIDT', '69n8hWNmelZfJymzUL6gAl']

def lambda_handler(event, context):
    params = event.get('queryStringParameters')
    mode = params.get('mode')
    id_list = get_artist_check(mode)
    print(id_list)
    if mode == 'artist':
        payload = neo_write(Artist, id_list)
        # if payload != []:
        #     invoke_email_lambda(payload)
        #     print('lambda invoked')
    elif mode == "playlist":
        payload = neo_write(Playlist, id_list)
    return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"{payload}"
        }),
        }

def neo_write(object, ids):
    new = []
    id_list = ids
    with driver.session() as session:
        for artist in id_list:
            current = object(artist['a.artist_id'])
            for item in current.get_final_items():
                try:
                    tx = session.execute_write(current.create_item, item)
                    nodes_created = tx[1].counters.nodes_created
                    if nodes_created != 0 and artist['check']:
                        new.append(item)
                except Exception as e:
                    print(e)
        emails = session.execute_read(Artist.get_artist_emails, new)
    return [{'album': album, 'emails': email['emails']} for album in new for email in emails if album['artists'][0]['artist_id'] == email['artist_id']]

def get_artist_check(mode):
    with driver.session() as session:
        if mode == 'artist':
            return session.execute_write(Artist.get_id_list)
        elif mode == "playlist":
            return session.execute_read(Playlist.get_id_list)
