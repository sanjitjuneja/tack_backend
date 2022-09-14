from aws.session_creater import create_smm_client, session_creater
from datetime import date, datetime

# ssm_client = boto3.client("ssm", region_name=AWS_REGION)
#
# get_response = ssm_client.get_parameters(
#     Names=['API_TOKEN_TEST_STAGE', "API_TOKEN"],
#     WithDecryption=True
# )
# print(get_response)
# for parameter in get_response.get("Parameters"):
#     print(parameter.get("Value"))
# Names=['API_TOKEN_TEST_STAGE', "API_TOKEN"]
#
# def json_datetime_serializer(obj):
#     if isinstance(obj, (datetime, date)):
#         return obj.isoformat()
#     raise TypeError("Type %s not serializable" % type(obj))
#
#
# test_token = json.dumps(
#     get_response['Parameter'],
#     indent=4,
#     default=json_datetime_serializer
# )
# print(get_response.get("Parameter").get("Value"))
# print(type(get_response))
# print(
#     json.dumps(get_response['Parameter'],
#                indent=4,
#                default= json_datetime_serializer))


def receive_setting_parameters(aws_access_key_id: str, aws_secret_access_key: str, aws_region: str) -> tuple:
    session = session_creater(aws_access_key_id, aws_secret_access_key, aws_region)
    client = create_smm_client(session, aws_region)
    response = client.get_parameters(
        Names=['ALLOWED_HOSTS', "CELERY_BROKER", "CHANNEL_LAYERS_HOST", "CSRF_TRUSTED_ORIGINS"],
        WithDecryption=True
    )
    allowed_hosts, celery_broker, channel_layers_host, crsf_trusted_origins = response.get("Parameters")
    return allowed_hosts, celery_broker, channel_layers_host, crsf_trusted_origins
