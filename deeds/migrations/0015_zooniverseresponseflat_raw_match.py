# Generated by Django 4.0.1 on 2022-01-24 16:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deeds', '0014_alter_zooniverseresponseflat_addition'),
    ]

    operations = [
        migrations.AddField(
            model_name='zooniverseresponseflat',
            name='raw_match',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='deeds.zooniverseresponseraw'),
        ),
    ]
