# Generated by Django 4.1.2 on 2022-11-02 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0023_alter_zooniverseresponseprocessed_buyer_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='bool_handwritten',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]