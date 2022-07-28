# Generated by Django 4.0.6 on 2022-07-28 14:29

from django.db import migrations, models
import racial_covenants_processor.storage_backends


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0008_deedpage_doc_alt_id_alter_deedpage_doc_num'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchhitreport',
            name='report_csv',
            field=models.FileField(null=True, storage=racial_covenants_processor.storage_backends.PublicMediaStorage(), upload_to='analysis/'),
        ),
    ]
