# Generated by Django 4.0 on 2023-02-27 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_auto_20210329_2217'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagemodel',
            name='is_call',
            field=models.BooleanField(default=False, verbose_name='Is call'),
        ),
    ]