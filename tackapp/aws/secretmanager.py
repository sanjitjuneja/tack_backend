import json
from aws.session_creater import create_secret_manager_client, session_creater


def receive_setting_secrets(aws_access_key_id: str, aws_secret_access_key: str, aws_region: str) -> dict:
    session = session_creater(aws_access_key_id, aws_secret_access_key, aws_region)
    client = create_secret_manager_client(session, aws_region)
    response = client.get_secret_value(
        SecretId='dev/tackapp/django'
    )
    return json.loads(response.get('SecretString'))
