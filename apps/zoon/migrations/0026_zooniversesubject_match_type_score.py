# Generated by Django 4.1.2 on 2022-11-02 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0025_alter_zooniverseresponseprocessed_match_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='zooniversesubject',
            name='match_type_score',
            field=models.FloatField(null=True),
        ),
    ]
