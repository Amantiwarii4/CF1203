# Generated by Django 3.2.6 on 2021-10-27 03:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_management', '0004_auto_20211026_0558'),
    ]

    operations = [
        migrations.AddField(
            model_name='chapterstatus',
            name='is_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='package',
            name='payment_link',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
