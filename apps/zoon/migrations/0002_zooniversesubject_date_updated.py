# Generated by Django 4.0.4 on 2022-04-14 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='zooniversesubject',
            name='date_updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]