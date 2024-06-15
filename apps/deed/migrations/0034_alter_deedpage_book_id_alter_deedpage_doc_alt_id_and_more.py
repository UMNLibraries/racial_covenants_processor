# Generated by Django 4.2.10 on 2024-03-10 04:04

from django.db import migrations, models
import racial_covenants_processor.storage_backends


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0033_deedpage_bool_manual'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deedpage',
            name='book_id',
            field=models.CharField(blank=True, db_index=True, max_length=103),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='doc_alt_id',
            field=models.CharField(blank=True, db_index=True, max_length=102),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='doc_num',
            field=models.CharField(blank=True, db_index=True, max_length=101),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='doc_type',
            field=models.CharField(blank=True, max_length=104),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='next_next_page_image_lookup',
            field=models.CharField(blank=True, max_length=203, null=True),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='next_next_page_image_web',
            field=models.ImageField(db_index=True, max_length=203, null=True, storage=racial_covenants_processor.storage_backends.PublicDeedStorage(), upload_to=''),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='next_page_image_lookup',
            field=models.CharField(blank=True, max_length=202, null=True),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='next_page_image_web',
            field=models.ImageField(db_index=True, max_length=202, null=True, storage=racial_covenants_processor.storage_backends.PublicDeedStorage(), upload_to=''),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='prev_page_image_lookup',
            field=models.CharField(blank=True, max_length=201, null=True),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='prev_page_image_web',
            field=models.ImageField(db_index=True, max_length=201, null=True, storage=racial_covenants_processor.storage_backends.PublicDeedStorage(), upload_to=''),
        ),
    ]