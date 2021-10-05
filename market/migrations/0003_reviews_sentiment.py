# Generated by Django 3.2.7 on 2021-10-05 22:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0002_auto_20211005_2157'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviews',
            name='sentiment',
            field=models.CharField(choices=[('Positive', 'Positive'), ('Negative', 'Negative'), ('Neutral', 'Neutral')], default=0, max_length=10),
            preserve_default=False,
        ),
    ]