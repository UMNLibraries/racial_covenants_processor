# Generated by Django 4.1.5 on 2023-03-31 20:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parcel', '0016_rename_subdivision_parcel_subdivision_spatial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='csvexport',
            options={'ordering': ('-id',)},
        ),
        migrations.AlterModelOptions(
            name='geojsonexport',
            options={'ordering': ('-id',)},
        ),
        migrations.AlterModelOptions(
            name='shpexport',
            options={'ordering': ('-id',)},
        ),
    ]
