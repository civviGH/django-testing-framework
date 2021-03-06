# Generated by Django 3.1b1 on 2020-12-16 14:13

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dtf', '0014_add_webhook'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebhookLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False)),
                ('trigger', models.CharField(choices=[('Submission', 'Submission'), ('TestResult', 'TestResult'), ('ReferenceSet', 'ReferenceSet'), ('TestReference', 'TestReference')], max_length=20)),
                ('request_url', models.URLField()),
                ('request_data', models.JSONField()),
                ('request_headers', models.JSONField()),
                ('response_status', models.IntegerField()),
                ('response_data', models.TextField()),
                ('response_headers', models.JSONField()),
                ('webhook', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='dtf.webhook')),
            ],
        ),
    ]