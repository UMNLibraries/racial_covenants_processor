# Generated by Django 4.1.2 on 2023-01-06 21:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0018_deedpage_id_workflow_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='deedpage',
            name='book_id',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
