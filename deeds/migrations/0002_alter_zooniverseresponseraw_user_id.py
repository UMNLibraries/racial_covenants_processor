# Generated by Django 4.0.1 on 2022-01-20 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deeds', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zooniverseresponseraw',
            name='user_id',
            field=models.IntegerField(null=True),
        ),
    ]
