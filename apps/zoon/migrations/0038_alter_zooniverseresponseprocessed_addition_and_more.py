# Generated by Django 4.1.5 on 2023-05-25 22:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0037_alter_zooniversesubject_addition_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='addition',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='block',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='buyer',
            field=models.CharField(blank=True, max_length=600, null=True),
        ),
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='city',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='lot',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='zooniverseresponseprocessed',
            name='seller',
            field=models.CharField(blank=True, max_length=600, null=True),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='addition',
            field=models.CharField(blank=True, default='', max_length=501),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='block',
            field=models.CharField(blank=True, default='', max_length=502),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='buyer',
            field=models.CharField(blank=True, default='', max_length=600),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='city',
            field=models.CharField(blank=True, default='', max_length=503),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='lot',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='seller',
            field=models.CharField(blank=True, default='', max_length=600),
            preserve_default=False,
        ),
    ]
