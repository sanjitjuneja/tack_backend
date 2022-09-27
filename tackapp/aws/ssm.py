from aws.session_creater import create_smm_client, session_creater


def receive_setting_parameters(aws_access_key_id: str, aws_secret_access_key: str, aws_region: str) -> tuple:
    session = session_creater(aws_access_key_id, aws_secret_access_key, aws_region)
    client = create_smm_client(session, aws_region)
    response = client.get_parameters(
        Names=['ALLOWED_HOSTS', "CELERY_BROKER", "CHANNEL_LAYERS_HOST", "CSRF_TRUSTED_ORIGINS"],
        WithDecryption=True
    )
    allowed_hosts, celery_broker, channel_layers_host, crsf_trusted_origins = response.get("Parameters")
    return allowed_hosts, celery_broker, channel_layers_host, crsf_trusted_origins
