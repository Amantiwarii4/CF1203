# Generated by Django 3.2.6 on 2021-11-18 05:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_management', '0008_certificate'),
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254)),
                ('subject', models.CharField(blank=True, max_length=500, null=True)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
