# Generated by Django 4.2.17 on 2025-01-17 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0053_alter_zooniversesubject_deedpage_doc_num'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='map_book',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='map_book_page',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
