import json, boto3, smtplib, ssl
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mako.template import Template

email_from = '' 
email_pass = ''

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

def send_email(email_to, course_name, amount, date, location):
    mail_template=Template(filename='mail_template.html', input_encoding='UTF-8')
    html = mail_template.render_unicode('tu beda zmienne')
    email_message = MIMEMultipart()
    email_message['From'], email_message['To'], email_message['Subject'] = email_from, email_to, "PLACEHOLDER"
    print(email_message)
    email_message.attach(MIMEText(html, "html"))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(email_from, email_pass)
        server.sendmail(email_from, email_to, email_message.as_string())

def lambda_handler(event, context):
    msg = ''
    params = event.get('queryStringParameters')
    send_email()
    return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"{msg}"
        }),
        }
