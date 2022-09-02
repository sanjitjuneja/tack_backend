import logging

import dwollav2

from tackapp.settings import DWOLLA_APP_KEY, DWOLLA_APP_SECRET, DWOLLA_WEBHOOK_SECRET

dwtoken = None


def save_dwolla_token(token):
    global dwtoken
    dwtoken = token


dwolla_client = dwollav2.Client(
    key=DWOLLA_APP_KEY,
    secret=DWOLLA_APP_SECRET,
    environment='sandbox',  # defaults to 'production'
    # requests={'timeout': 0.001},
    on_grant=lambda t: save_dwolla_token(t)
)

webhook_request = {
  'url': 'http://44.203.217.242/api/v1/webhooks/dwolla/',
  'secret': DWOLLA_WEBHOOK_SECRET
}
# webhook_request = {
#   'url': 'https://zgqcy9sg1g.execute-api.us-east-1.amazonaws.com/DwollaTest',
#   'secret': DWOLLA_WEBHOOK_SECRET
# }

token = dwolla_client.Auth.client()


# token.delete("webhook-subscriptions/f666b8f9-9800-4f64-bcc8-a1ceceb7f061")
# subscriptions = token.get('webhook-subscriptions')
# print(subscriptions)
# pprint(subscriptions.body)
# print(subscriptions.headers)
subscription = token.post('webhook-subscriptions', webhook_request)
logging.getLogger().warning(f"{subscription = }")
# logging.getLogger().warning(subscription)
# print(subscription)
# print(subscription.body)
# print(subscription.headers)

