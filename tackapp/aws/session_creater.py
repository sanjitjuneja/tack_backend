import boto3
# from tackapp.settings import AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID, AWS_REGION
import json
import environ
import os
from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent
# env = environ.Env(DEBUG=(bool, True))
# environ.Env.read_env(os.path.join(BASE_DIR, "dev.env"))
#
# AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
# AWS_REGION = env("AWS_REGION")
#
# session = boto3.Session(
#     aws_access_key_id=AWS_ACCESS_KEY_ID,
#     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
#     region_name=AWS_REGION,
# )
#
# secret_manager_client = session.client(service_name="secretsmanager", region_name=AWS_REGION)


def session_creater(aws_access_key_id: str, aws_secret_access_key: str, aws_region: str):
    return boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region,
    )


def create_secret_manager_client(session, aws_region):
    return session.client(service_name="secretsmanager", region_name=aws_region)


def create_smm_client(session, aws_region):
    return session.client(service_name="ssm", region_name=aws_region)
