from django.apps import AppConfig


class TackConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tack"

    def ready(self):
        from . import signals
        from django.contrib import admin
        from django.contrib.auth.models import Group
        from djstripe.models import Account, APIKey, ApplicationFeeRefund, ApplicationFee, BankAccount, Coupon, Dispute, File, FileLink, IdempotencyKey, Invoice, Mandate, Plan, Price, Product, Refund, Session, Source, Subscription, TaxRate, TransferReversal, Transfer, UsageRecord, UsageRecordSummary

        admin.site.unregister(Group)
        admin.site.unregister([Account, APIKey, ApplicationFeeRefund, ApplicationFee, BankAccount, Coupon, Dispute, File, FileLink, IdempotencyKey, Invoice, Mandate, Plan, Price, Product, Refund, Session, Source, Subscription, TaxRate, TransferReversal, Transfer, UsageRecord, UsageRecordSummary])
