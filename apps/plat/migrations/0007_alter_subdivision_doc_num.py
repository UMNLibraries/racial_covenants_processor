# Generated by Django 4.1.5 on 2023-06-07 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plat', '0006_subdivisionalternatename'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subdivision',
            name='doc_num',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
    ]
