# Generated by Django 4.2.14 on 2024-07-11 22:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0046_alter_manualcovenant_lot'),
        ('parcel', '0022_rename_docs_count_allcovenanteddocscsvexport_doc_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parcel',
            name='workflow',
            field=models.ForeignKey(help_text='Testing documentation', null=True, on_delete=django.db.models.deletion.SET_NULL, to='zoon.zooniverseworkflow'),
        ),
    ]
