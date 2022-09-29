import logging

import dwollav2

from tackapp.settings import DWOLLA_APP_KEY, DWOLLA_APP_SECRET

dwtoken = None


def save_dwolla_token(token):
    global dwtoken
    dwtoken = token


dwolla_client = dwollav2.Client(
    key=DWOLLA_APP_KEY,
    secret=DWOLLA_APP_SECRET,
    # environment='sandbox',  # defaults to 'production'
    # requests={'timeout': 0.001},
    on_grant=lambda t: save_dwolla_token(t)
)
