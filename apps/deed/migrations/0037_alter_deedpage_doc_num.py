# Generated by Django 4.2.10 on 2024-03-10 22:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0036_alter_deedpage_doc_num'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deedpage',
            name='doc_num',
            field=models.CharField(blank=True, db_index=True, max_length=101),
        ),
    ]