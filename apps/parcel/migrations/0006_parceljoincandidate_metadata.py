# Generated by Django 4.0.4 on 2022-04-18 22:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parcel', '0005_parceljoincandidate'),
    ]

    operations = [
        migrations.AddField(
            model_name='parceljoincandidate',
            name='metadata',
            field=models.JSONField(blank=True, null=True),
        ),
    ]