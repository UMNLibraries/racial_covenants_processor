# Generated by Django 4.2.5 on 2023-09-29 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0030_remove_deedpage_next_deedpage_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deedpage',
            name='next_next_page_image_lookup',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='deedpage',
            name='next_page_image_lookup',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='deedpage',
            name='prev_page_image_lookup',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
