from celery import shared_task
from django.db import transaction

from payment.models import DwollaRemovedAccount
from payment.services import is_user_have_dwolla_pending_transfers
from user.services import deactivate_dwolla_account


@shared_task
def check_dwolla_removed_customers():
    removed_customers = DwollaRemovedAccount.objects.all()
    for customer in removed_customers:
        if not is_user_have_dwolla_pending_transfers(customer.dwolla_id):
            deactivate_and_delete_removed_customer(customer)


@transaction.atomic
def deactivate_and_delete_removed_customer(customer):
    deactivate_dwolla_account(customer.dwolla_id)
    customer.delete()
