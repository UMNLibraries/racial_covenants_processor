# Generated by Django 4.0.5 on 2022-07-14 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0004_searchhitreport_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='deedpage',
            name='s3_lookup',
            field=models.CharField(blank=True, db_index=True, max_length=500),
        ),
    ]
