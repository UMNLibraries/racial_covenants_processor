# Generated by Django 4.0.4 on 2022-04-21 00:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0005_remove_zooniversesubject_join_strings_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zooniversesubject',
            name='join_candidates',
            field=models.JSONField(blank=True, max_length=500, null=True),
        ),
    ]
