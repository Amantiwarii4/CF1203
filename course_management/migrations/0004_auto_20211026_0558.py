# Generated by Django 3.2.6 on 2021-10-26 05:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_management', '0003_banner'),
    ]

    operations = [
        migrations.CreateModel(
            name='Services',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=100)),
                ('image', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('link', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Upcomingevents',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=100)),
                ('about', models.TextField(blank=True, null=True, verbose_name='about')),
                ('image', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('link', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='banner',
            name='link',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
