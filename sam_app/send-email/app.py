import json, boto3, smtplib, ssl
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mako.template import Template
from itertools import groupby

email_from = '' 
email_pass = ''

def lambda_handler(event, context):
    new_tracks = json.loads(event['message'])
    if new_tracks != []:
        for user in new_tracks:
            send_email(user['email'], user['albumlist'])
    return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Success!"
        }),
        }

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

def parse_to_send(data):
    def key(k):
        return k['email']
    split = []

    for l in data:
        emails = l['emails']
        del l['emails']
        for email in emails:
            split.append({'email': email, 'album': l['album']})

    split = sorted(split, key=key)
    return [{'email': key, 'albumlist': list(value)} for key, value in groupby(split, key=key)]

def send_email(email_to, new_tracks):
    mail_template=Template(filename='mail_template.html',input_encoding='utf-8', output_encoding='utf-8', encoding_errors='replace')
    html = mail_template.render_unicode(x=new_tracks)
    email_message = MIMEMultipart()
    email_message['From'], email_message['To'], email_message['Subject'] = email_from, email_to, "PLACEHOLDER"
    print(email_message)
    email_message.attach(MIMEText(html, "html"))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(email_from, email_pass)
        server.sendmail(email_from, email_to, email_message.as_string())
