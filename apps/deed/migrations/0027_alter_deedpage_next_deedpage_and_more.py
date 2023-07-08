# Generated by Django 4.1.5 on 2023-07-07 21:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deed', '0026_deedpage_next_deedpage_deedpage_next_next_deedpage_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deedpage',
            name='next_deedpage',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='next_deedpage_set', to='deed.deedpage'),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='next_next_deedpage',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='next_next_deedpage_set', to='deed.deedpage'),
        ),
        migrations.AlterField(
            model_name='deedpage',
            name='prev_deedpage',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='prev_deedpage_set', to='deed.deedpage'),
        ),
    ]
