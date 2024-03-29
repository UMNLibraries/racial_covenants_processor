# Generated by Django 4.1.5 on 2023-02-16 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0027_alter_zooniversesubject_deedpage_s3_lookup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zooniversesubject',
            name='buyer',
            field=models.CharField(blank=True, max_length=126),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='buyer_final',
            field=models.CharField(blank=True, max_length=126, null=True, verbose_name='Buyer name'),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='seller',
            field=models.CharField(blank=True, max_length=125),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='seller_final',
            field=models.CharField(blank=True, max_length=125, null=True, verbose_name='Seller name'),
        ),
    ]
