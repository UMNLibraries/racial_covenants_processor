# Generated by Django 4.0.6 on 2022-08-10 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0016_remove_manualcovenant_street_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='manualcovenant',
            name='doc_num',
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='manualcovenant',
            name='cov_type',
            field=models.CharField(blank=True, choices=[('PS', 'Public submission (single property)'), ('SE', 'Something else'), ('PT', 'Plat covenant')], max_length=4, null=True),
        ),
    ]
