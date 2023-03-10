# Generated by Django 3.1.7 on 2021-03-29 22:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import chat.models
import uuid


def null_file(apps, schema_editor):
    # We can't import the MessageModel model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    mm = apps.get_model('chat', 'MessageModel')
    for message in mm.all_objects.all():
        message.file = None
        message.save()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(null_file),
        migrations.CreateModel(
            name='UploadedFile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file',
                 models.FileField(upload_to=chat.models.user_directory_path, verbose_name='File')),
                ('upload_date', models.DateTimeField(auto_now_add=True, verbose_name='Upload date')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+',
                                                  to=settings.AUTH_USER_MODEL, verbose_name='Uploaded_by')),
            ],
        ),
        migrations.AlterField(
            model_name='messagemodel',
            name='file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING,
                                    related_name='message', to='chat.uploadedfile',
                                    verbose_name='File'),
        ),
    ]
