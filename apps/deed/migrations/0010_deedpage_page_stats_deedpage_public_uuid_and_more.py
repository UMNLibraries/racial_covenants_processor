# Generated by Django 4.0.6 on 2022-08-15 00:45

from django.db import migrations, models
import racial_covenants_processor.storage_backends


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0009_alter_searchhitreport_report_csv'),
    ]

    operations = [
        migrations.AddField(
            model_name='deedpage',
            name='page_stats',
            field=models.FileField(null=True, storage=racial_covenants_processor.storage_backends.PrivateMediaStorage(), upload_to=''),
        ),
        migrations.AddField(
            model_name='deedpage',
            name='public_uuid',
            field=models.CharField(blank=True, db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='page_image_web',
            field=models.ImageField(null=True, storage=racial_covenants_processor.storage_backends.PublicDeedStorage(), upload_to=''),
        ),
    ]
