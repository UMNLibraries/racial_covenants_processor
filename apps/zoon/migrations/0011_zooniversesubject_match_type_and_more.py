# Generated by Django 4.0.4 on 2022-05-12 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0010_manualcorrection_match_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='zooniversesubject',
            name='match_type',
            field=models.CharField(blank=True, choices=[('SL', 'Simple lot'), ('ML', 'Multiple single lots'), ('PL', 'Partial lot'), ('PD', 'Long phys description'), ('C', 'Cemetery plot'), ('PC', 'Petition covenant'), ('SE', 'Something else'), ('NG', 'No geographic information')], max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='bool_covenant_final',
            field=models.BooleanField(null=True, verbose_name='Racial covenant?'),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='bool_manual_correction',
            field=models.BooleanField(default=False, null=True, verbose_name='Manual updates?'),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='bool_parcel_match',
            field=models.BooleanField(default=False, verbose_name='Parcel match?'),
        ),
    ]