from classes import Artist, Playlist
import json
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

NEO4J_CREDS = get_secret('neo4j-creds')
uri, user, password = NEO4J_CREDS['NEO4J_URI'], NEO4J_CREDS['NEO4J_USERNAME'], NEO4J_CREDS['NEO4J_PASSWORD']
driver = GraphDatabase.driver(uri, auth=(user, password))

playlist_ids = ['4ul6VwbC9q89M3FAs8fOdb', '5dtDRRVVYQSnBsKNAzlDLo', '5037GRVTAdYiQvGRpzWIDT', '69n8hWNmelZfJymzUL6gAl']

def lambda_handler(event, context):
    msg = ''
    params = event.get('queryStringParameters')
    mode = params.get('mode')
    if mode == 'artist':
        firstrun = eval(params.get('f'))
        msg = 'artist'
        payload = Artist.neo_write(Artist, firstrun)
        if payload != []:
            invoke_email_lambda(payload)
            print('lambda invoked')
    elif mode == "playlist":
        msg = 'playlist'
        Artist.neo_write(Playlist)
    return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"{msg}"
        }),
        }

def invoke_email_lambda(new_tracks):
    lnvoke_lam = boto3.client("lambda", region_name='eu-central-1')
    payload = {'message': json.dumps(new_tracks)}
    response = lnvoke_lam.invoke(FunctionName="arn:aws:lambda:eu-central-1:529336170453:function:sam-app-SendEmailFunction-3UgqZ4QN5w68",
    InvocationType="Event", Payload=json.dumps(payload))
