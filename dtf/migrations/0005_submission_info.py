# Generated by Django 3.1b1 on 2020-09-22 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dtf', '0004_auto_20200921_1525'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='info',
            field=models.JSONField(default=dict),
        ),
    ]
