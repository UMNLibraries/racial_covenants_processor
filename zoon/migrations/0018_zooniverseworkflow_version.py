# Generated by Django 4.0.3 on 2022-03-18 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0017_alter_zooniverseresponseprocessed_response_raw'),
    ]

    operations = [
        migrations.AddField(
            model_name='zooniverseworkflow',
            name='version',
            field=models.FloatField(null=True),
        ),
    ]
