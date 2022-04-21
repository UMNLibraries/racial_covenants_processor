# Generated by Django 4.0.4 on 2022-04-20 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0002_zooniversesubject_date_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='manualcorrection',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='manualcorrection',
            name='street_address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='zooniversesubject',
            name='city_final',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='City'),
        ),
        migrations.AddField(
            model_name='zooniversesubject',
            name='street_address_final',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Street address'),
        ),
    ]
