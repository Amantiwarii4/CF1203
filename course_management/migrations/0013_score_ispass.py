# Generated by Django 3.2.6 on 2021-11-26 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_management', '0012_payments'),
    ]

    operations = [
        migrations.AddField(
            model_name='score',
            name='ispass',
            field=models.BooleanField(default=False),
        ),
    ]
