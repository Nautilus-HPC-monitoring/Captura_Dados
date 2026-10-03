import os
import boto3 as boto
from dotenv import load_dotenv


load_dotenv()
session = boto.Session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
    region_name=os.getenv('REGION_NAME')
)

s3_client = session.client("s3")