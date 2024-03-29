# Generated by Django 4.1.2 on 2023-01-11 21:33

from django.db import migrations, models
import racial_covenants_processor.storage_backends


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0021_alter_deedpage_batch_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deedpage',
            name='page_image_web',
            field=models.ImageField(max_length=200, null=True, storage=racial_covenants_processor.storage_backends.PublicDeedStorage(), upload_to=''),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='page_ocr_json',
            field=models.FileField(max_length=200, null=True, storage=racial_covenants_processor.storage_backends.PrivateMediaStorage(), upload_to=''),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='page_ocr_text',
            field=models.FileField(max_length=200, null=True, storage=racial_covenants_processor.storage_backends.PrivateMediaStorage(), upload_to=''),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='page_stats',
            field=models.FileField(max_length=200, null=True, storage=racial_covenants_processor.storage_backends.PrivateMediaStorage(), upload_to=''),
        ),
    ]
