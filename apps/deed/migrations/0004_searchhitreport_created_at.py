# Generated by Django 4.0.5 on 2022-07-14 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0003_searchhitreport_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchhitreport',
            name='created_at',
            field=models.DateTimeField(default='1900-01-01'),
            preserve_default=False,
        ),
    ]