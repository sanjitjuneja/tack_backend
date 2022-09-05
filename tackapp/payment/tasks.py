# from celery import shared_task
#
# from user.services import is_user_have_dwolla_pending_transfers
#

# @shared_task
# def check_removed_dwolla_accounts():
#     removed_accounts = DwollaRemovedAccount.objects.all()
#     for account in removed_accounts:
#         if not is_user_have_dwolla_pending_transfers(account.dwolla_id):
#
