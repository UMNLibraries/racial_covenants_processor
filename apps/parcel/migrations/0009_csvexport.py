# Generated by Django 4.0.4 on 2022-05-19 22:34

from django.db import migrations, models
import django.db.models.deletion
import racial_covenants_processor.storage_backends


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0012_zooniversesubject_parcel_addresses_and_more'),
        ('parcel', '0008_shpexport'),
    ]

    operations = [
        migrations.CreateModel(
            name='CSVExport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csv', models.FileField(null=True, storage=racial_covenants_processor.storage_backends.PublicMediaStorage(), upload_to='main_exports/')),
                ('covenant_count', models.IntegerField()),
                ('created_at', models.DateTimeField()),
                ('workflow', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='zoon.zooniverseworkflow')),
            ],
        ),
    ]
