from django.db import transaction

from tack.models import Tack


@transaction.atomic
def send_payment_to_runner(tack: Tack):
    if not tack.is_paid:
        # TODO: Call Venmo API
        tack.runner.bankaccount.usd_balance += tack.price
        tack.is_paid = True
        tack.save()
