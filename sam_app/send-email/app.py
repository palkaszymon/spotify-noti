import json, boto3, smtplib, ssl
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mako.template import Template
from itertools import groupby

email_from = 'lilpalabeats@gmail.com' 
email_pass = 'hhqprhkwtfkyefva'

def lambda_handler(event, context):
    new_tracks = parse_to_send(json.loads(event['message']))
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

new_tracks = [{'email': 'bigspeep@gmail.com', 'album': {'id': '29d8dGxvF4gdkPwZI4f5Ub', 'name': 'AftërLyfe', 'type': 'album', 'artists': [{'artist_name': 'Yeat', 'artist_id': '3qiHUAX7zY4Qnjx8TNUzVx'}], 'release_date': '2023-02-24'}}, {'email': 'bigspeep@gmail.com', 'album': {'id': '4t1a5i9dBXSbEyJQn9qBIj', 'name': 'Lyfë', 'type': 'album', 'artists': [{'artist_name': 'Yeat', 'artist_id': '3qiHUAX7zY4Qnjx8TNUzVx'}], 'release_date': '2022-09-08'}}, {'email': 'bigspeep@gmail.com', 'album': {'id': '6p9X1sDMPODAqn3r5RpAjA', 'name': 'Talk', 'type': 'single', 'artists': [{'artist_name': 'Yeat', 'artist_id': '3qiHUAX7zY4Qnjx8TNUzVx'}], 'release_date': '2022-09-01'}}, {'email': 'bigspeep@gmail.com', 'album': {'id': '1lcm0KMxBCd2Dk1wu06B6G', 'name': 'Tu cie mam (Psychoza)', 'type': 'single', 'artists': [{'artist_name': 'Stock Wudeczka', 'artist_id': '0ClgZqBaZrO0167WwBgK2g'}], 'release_date': '2021-09-10'}}, {'email': 'bigspeep@gmail.com', 'album': {'id': '1DTcETj3MdLok15v7hEYKg', 'name': 'Mam nadzieje że Young Leosia tego nie usłyszy lol', 'type': 'single', 'artists': [{'artist_name': 'Stock Wudeczka', 'artist_id': '0ClgZqBaZrO0167WwBgK2g'}], 'release_date': '2021-09-10'}}, {'email': 'bigspeep@gmail.com', 'album': {'id': '3iBksIffjadocPMD8C5Gl7', 'name': 'Kocha Moj Kastet (Remix)', 'type': 'single', 'artists': [{'artist_name': 'Stock Wudeczka', 'artist_id': '0ClgZqBaZrO0167WwBgK2g'}], 'release_date': '2021-03-12'}}, {'email': 'bigspeep@gmail.com', 'album': {'id': '2JQBEHdiOEl03JnbxHdHY0', 'name': 'STO GRADOWYCH CHMUR', 'type': 'single', 'artists': [{'artist_name': 'Czerwone Gitary', 'artist_id': '4wck1fvaBpmJNFaeDT1Laa'}], 'release_date': '2021-10-22'}}, {'email': 'bigspeep@gmail.com', 'album': {'id': '2dZ85hQdPxS4wDiwCoHqJi', 'name': 'Raz do roku', 'type': 'single', 'artists': [{'artist_name': 'Czerwone Gitary', 'artist_id': '4wck1fvaBpmJNFaeDT1Laa'}], 'release_date': '2019-11-06'}}, {'email': 'bigspeep@gmail.com', 'album': {'id': '0zIUMed7yYXAsoFOGA9gqC', 'name': 'Wspominam Białe Święta', 'type': 'single', 'artists': [{'artist_name': 'Czerwone Gitary', 'artist_id': '4wck1fvaBpmJNFaeDT1Laa'}], 'release_date': '2017-11-20'}}]

mail_template=Template(filename=r'C:\Users\bigsp\Desktop\personal\spotify-noti\sam_app\send-email\mail_template.html',input_encoding='utf-16', output_encoding='utf-16', encoding_errors='replace')
html = mail_template.render_unicode(x=new_tracks)
with open('test.html', 'w') as f:
    f.write(html)