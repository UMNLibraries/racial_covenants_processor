# Generated by Django 4.0.4 on 2022-05-19 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0011_zooniversesubject_match_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='zooniversesubject',
            name='parcel_addresses',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='zooniversesubject',
            name='parcel_city',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
    ]