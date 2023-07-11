# Generated by Django 4.1.5 on 2023-02-01 16:04

from django.db import migrations, models
import racial_covenants_processor.storage_backends


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0024_deedpage_doc_page_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='deedpage',
            name='next_next_page_image_web',
            field=models.ImageField(db_index=True, max_length=200, null=True, storage=racial_covenants_processor.storage_backends.PublicDeedStorage(), upload_to=''),
        ),
        migrations.AddField(
            model_name='deedpage',
            name='next_page_image_web',
            field=models.ImageField(db_index=True, max_length=200, null=True, storage=racial_covenants_processor.storage_backends.PublicDeedStorage(), upload_to=''),
        ),
        migrations.AddField(
            model_name='deedpage',
            name='prev_page_image_web',
            field=models.ImageField(db_index=True, max_length=200, null=True, storage=racial_covenants_processor.storage_backends.PublicDeedStorage(), upload_to=''),
        ),
    ]
