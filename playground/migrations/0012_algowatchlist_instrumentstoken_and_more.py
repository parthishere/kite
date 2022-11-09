# Generated by Django 4.1.2 on 2022-11-05 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('playground', '0011_algowatchlist_instruments_manualwatchlist_positions'),
    ]

    operations = [
        migrations.AddField(
            model_name='algowatchlist',
            name='instrumentsToken',
            field=models.CharField(default='1111', max_length=100),
        ),
        migrations.AddField(
            model_name='manualwatchlist',
            name='instrumentsToken',
            field=models.CharField(default='1111', max_length=100),
        ),
        migrations.AddField(
            model_name='positions',
            name='instrumentsToken',
            field=models.CharField(default='1111', max_length=100),
        ),
    ]
