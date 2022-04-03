# Generated by Django 4.0.3 on 2022-03-31 07:01

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('v1', '0004_rename_text_post_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='profileImage',
            field=models.CharField(db_column='profile_image', max_length=255, null=True, verbose_name='profile_image'),
        ),
        migrations.AddField(
            model_name='post',
            name='userName',
            field=models.CharField(db_column='user_name', default='', max_length=255, verbose_name='user_name'),
        ),
        migrations.AddField(
            model_name='post',
            name='writeTime',
            field=models.DateField(default=datetime.datetime(2022, 3, 31, 7, 1, 3, 272489, tzinfo=utc)),
        ),
    ]