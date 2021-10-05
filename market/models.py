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
    balance = models.IntegerField()

class Fiat_Transactions(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None, null=True)
    transaction_types = [('Withdrawal', 'Withdrawal'), ('Deposit','Deposit'), ('Buy','Buy'), ('Sell','Sell')]

    userid = models.CharField(max_length=10)
    date = models.CharField(max_length=10)
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=10, choices=transaction_types)
    notes = models.CharField(max_length=200, blank=True)

class User_Requests(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None, null=True)
    request_type = [('Deposit','Deposit'), ('Withdraw', 'Withdraw')]
    status_type = [('Pending','Pending'), ('Completed', 'Completed'), ('Rejected', 'Rejected')]

    userid = models.CharField(max_length=10)
    amount = models.IntegerField()
    request = models.CharField(max_length=10, choices=request_type)
    reference = models.CharField(max_length=12)
    bank_name = models.CharField(max_length=50, default="Nedbank")
    account_number = models.CharField(max_length=50, default="0")
    proof = models.ImageField(upload_to='uploads/proof/%Y/%m/%d/', max_length=50)
    date = models.CharField(max_length=10)
    status = models.CharField(max_length=10, choices=status_type)