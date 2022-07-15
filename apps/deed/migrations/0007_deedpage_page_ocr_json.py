# Generated by Django 4.0.5 on 2022-07-15 00:49

from django.db import migrations, models
import racial_covenants_processor.storage_backends


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0006_matchterm_remove_deedpage_matched_terms_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deedpage',
            name='page_ocr_json',
            field=models.FileField(null=True, storage=racial_covenants_processor.storage_backends.PrivateMediaStorage(), upload_to=''),
        ),
    ]
