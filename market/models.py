from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Create your models here.

class CustomUser(AbstractUser):
    public_key = models.CharField(max_length=100)
    private_key = models.CharField(max_length=100)

class Btc_Details(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None, null=True)
    private_key = models.CharField(max_length=100)
    public_key = models.CharField(max_length=100)
    balance_btc = models.CharField(max_length=50)
    balance_usd = models.CharField(max_length=50)
    transactions = models.CharField(max_length=10000, blank=True)

class Fiat_Details(models.Model):
    # Balance in USD
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None, null=True)
    balance = models.CharField(max_length=50)

class Fiat_Transactions(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None, null=True)
    transaction_types = [('Withdrawal', 'Withdrawal'), ('Deposit','Deposit')]

    date = models.CharField(max_length=10)
    amount = models.CharField(max_length=50)
    transaction_type = models.CharField(max_length=10, choices=transaction_types)
    notes = models.CharField(max_length=200, blank=True)
