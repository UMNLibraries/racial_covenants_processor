# Generated by Django 4.1.2 on 2022-11-02 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0022_alter_zooniversesubject_bool_handwritten'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='buyer',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='seller',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]