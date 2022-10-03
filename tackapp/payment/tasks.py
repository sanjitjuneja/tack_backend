from celery import shared_task
from django.db.models import F

from payment.models import Transaction


@shared_task
def calculate_fee_difference_for_transaction_model():
    transactions = Transaction.objects.filter(service_fee=None)
    transactions.update(
        fee_difference=F('amount_with_fees') - F('amount_requested') - F('service_fee')
    )
