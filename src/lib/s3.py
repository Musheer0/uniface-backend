import boto3
import os
from dotenv import load_dotenv

load_dotenv()

bucket = os.getenv("S3_BUCKET")

s3 = boto3.client("s3")