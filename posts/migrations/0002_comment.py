# Generated by Django 4.0 on 2023-03-12 18:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0022_delete_provider'),
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content', models.TextField()),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posts.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.user')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
