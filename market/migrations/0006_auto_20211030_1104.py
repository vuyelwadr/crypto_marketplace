# Generated by Django 3.2.7 on 2021-10-30 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0005_fiat_details_account_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fiat_details',
            name='account_number',
            field=models.CharField(default='None', max_length=20),
        ),
        migrations.AlterField(
            model_name='fiat_details',
            name='bank_details',
            field=models.CharField(default='None', max_length=50),
        ),
    ]
