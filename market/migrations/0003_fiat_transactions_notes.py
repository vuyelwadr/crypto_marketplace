# Generated by Django 3.2.7 on 2021-09-20 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0002_fiat_transactions'),
    ]

    operations = [
        migrations.AddField(
            model_name='fiat_transactions',
            name='notes',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
