# Generated by Django 4.0.1 on 2022-02-01 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0009_zooniversesubject_bool_problem'),
    ]

    operations = [
        migrations.AddField(
            model_name='zooniversesubject',
            name='image_id',
            field=models.CharField(db_index=True, default='', max_length=100),
            preserve_default=False,
        ),
    ]
