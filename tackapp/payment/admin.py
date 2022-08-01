from django.contrib import admin
from .models import BankAccount, UserPaymentMethods

admin.site.register(BankAccount)
admin.site.register(UserPaymentMethods)
