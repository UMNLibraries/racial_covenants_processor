# Generated by Django 4.1.5 on 2023-07-10 18:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0027_auto_20230710_1346'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deedpage',
            name='prev_deedpage_2',
        ),
    ]
