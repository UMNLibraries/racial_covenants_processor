# Generated by Django 4.2.5 on 2023-09-29 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0039_alter_zooniverseworkflow_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='zooniversesubject',
            name='image_links',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
