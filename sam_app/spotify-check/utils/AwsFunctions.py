import boto3
from botocore.exceptions import ClientError
import json

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

def invoke_email_lambda(new_tracks):
    lnvoke_lam = boto3.client("lambda", region_name='eu-central-1')
    payload = {'message': json.dumps(new_tracks)}
    response = lnvoke_lam.invoke(FunctionName="arn:aws:lambda:eu-central-1:529336170453:function:notifymusic-SendEmailFunction-xET28YEP0G2t",
    InvocationType="Event", Payload=json.dumps(payload))