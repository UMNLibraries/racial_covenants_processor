# Generated by Django 4.0.4 on 2022-04-18 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parcel', '0003_parcel_plat'),
    ]

    operations = [
        migrations.AddField(
            model_name='parcel',
            name='plat_standardized',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
