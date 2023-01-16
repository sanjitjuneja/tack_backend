import plaid
from plaid.api import plaid_api

from tackapp.settings import PLAID_CLIENT_ID, PLAID_CLIENT_SECRET

configuration = plaid.Configuration(
    host=plaid.Environment.Production,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_CLIENT_SECRET
    }
)

api_client = plaid.ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)
