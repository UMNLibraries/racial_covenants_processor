# Generated by Django 4.0.3 on 2022-03-17 21:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0016_alter_zooniverseresponseprocessed_bool_covenant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='response_raw',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='zoon.zooniverseresponseraw'),
        ),
    ]