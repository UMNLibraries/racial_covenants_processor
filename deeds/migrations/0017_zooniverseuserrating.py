# Generated by Django 4.0.1 on 2022-01-26 22:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deeds', '0016_alter_zooniverseresponseflat_raw_match'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZooniverseUserRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cohen_kappa', models.FloatField(null=True)),
                ('n_clfs', models.IntegerField(null=True)),
                ('reliability_score', models.FloatField(null=True)),
                ('rank', models.IntegerField(null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='deeds.zooniverseuser')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='deeds.workflow')),
            ],
        ),
    ]
