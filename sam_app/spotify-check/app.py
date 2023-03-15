from utils.Classes import Artist, Playlist
from utils.AwsFunctions import get_secret, invoke_email_lambda
import json
from neo4j import GraphDatabase
from time import time

NEO4J_CREDS = get_secret('neo4j-creds')
uri, user, password = NEO4J_CREDS['NEO4J_URI'], NEO4J_CREDS['NEO4J_USERNAME'], NEO4J_CREDS['NEO4J_PASSWORD']
driver = GraphDatabase.driver(uri, auth=(user, password))

def lambda_handler(event, context):
    id_list = get_artist_check('artist')
    payload = neo_write(Artist, id_list)
    if payload != []:
        invoke_email_lambda(payload)
        print('lambda invoked')
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
        st = time()
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
        et = time()
        print(f"Succesfully checked {len(id_list)} artists, in {et-st}.")
        emails = session.execute_read(Artist.get_artist_emails, new)
    return [{'album': album, 'emails': email['emails']} for album in new for email in emails if album['artists'][0]['artist_id'] == email['artist_id']]

def get_artist_check(mode):
    with driver.session() as session:
        if mode == 'artist':
            return session.execute_write(Artist.get_id_list)
        elif mode == "playlist":
            return session.execute_read(Playlist.get_id_list)

driver.close()