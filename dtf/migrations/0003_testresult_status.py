# Generated by Django 3.1b1 on 2020-08-13 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dtf', '0002_auto_20200813_1201'),
    ]

    operations = [
        migrations.AddField(
            model_name='testresult',
            name='status',
            field=models.CharField(choices=[('successful', 'successful'), ('unstable', 'unstable'), ('unknown', 'unknown'), ('failed', 'failed'), ('broken', 'broken')], default='unknown', max_length=20),
        ),
    ]
