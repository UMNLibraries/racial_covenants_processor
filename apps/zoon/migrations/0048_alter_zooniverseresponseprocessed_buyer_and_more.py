# Generated by Django 4.2.15 on 2024-09-13 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0047_manualcovenant_parcel_addresses_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='buyer',
            field=models.CharField(blank=True, max_length=900, null=True),
        ),
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='seller',
            field=models.CharField(blank=True, max_length=900, null=True),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='buyer',
            field=models.CharField(blank=True, max_length=900),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='buyer_final',
            field=models.CharField(blank=True, max_length=900, null=True, verbose_name='Buyer name'),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='seller',
            field=models.CharField(blank=True, max_length=900),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='seller_final',
            field=models.CharField(blank=True, max_length=900, null=True, verbose_name='Seller name'),
        ),
    ]
