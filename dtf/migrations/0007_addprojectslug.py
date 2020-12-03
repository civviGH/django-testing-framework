# Generated by Django 3.1b1 on 2020-12-03 10:13

from django.db import migrations, models
from django.utils.text import slugify

def generate_default_project_slugs(apps, schema_editor):
    Project = apps.get_model('dtf', 'Project')
    for project in Project.objects.all().iterator():
        project.slug = slugify(project.name)
        project.save()

class Migration(migrations.Migration):

    dependencies = [
        ('dtf', '0006_auto_20201002_1125'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='slug',
            field=models.SlugField(null=True, max_length=40),
        ),
        migrations.RunPython(generate_default_project_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='project',
            name='slug',
            field=models.SlugField(max_length=40, unique=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
