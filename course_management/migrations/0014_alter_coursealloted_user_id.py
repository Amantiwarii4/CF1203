# Generated by Django 3.2.6 on 2021-09-04 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_management', '0013_alter_coursealloted_category_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursealloted',
            name='user_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='user_id'),
        ),
    ]