# Generated by Django 4.2.10 on 2024-03-12 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0041_alter_zooniverseresponseprocessed_subject'),
    ]

    operations = [
        migrations.AddField(
            model_name='zooniverseworkflow',
            name='slug',
            field=models.CharField(db_index=True, default='', max_length=100),
            preserve_default=False,
        ),
    ]