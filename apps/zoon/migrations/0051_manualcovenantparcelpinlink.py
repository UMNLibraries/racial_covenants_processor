# Generated by Django 4.2.16 on 2024-12-03 21:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('zoon', '0050_manualparcelpinlink'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManualCovenantParcelPINLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parcel_pin', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('comments', models.TextField(blank=True, null=True)),
                ('manual_covenant', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='zoon.manualcovenant')),
                ('workflow', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='zoon.zooniverseworkflow')),
            ],
        ),
    ]
