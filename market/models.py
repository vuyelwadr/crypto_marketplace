from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    public_key = models.CharField(max_length=100, blank=True)
    private_key = models.CharField(max_length=100, blank=True)
