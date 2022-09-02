import logging

from payment.dwolla_service import dwolla_client
from tackapp.settings import DWOLLA_WEBHOOK_SECRET

token = dwolla_client.Auth.client()
webhook_request = {
  'url': 'http://44.203.217.242/api/v1/webhooks/dwolla/',
  'secret': DWOLLA_WEBHOOK_SECRET
}
subscription = token.post('webhook-subscriptions', webhook_request)
logging.getLogger().warning(f"{subscription = }")
