# Generated by Django 4.1.1 on 2023-05-11 08:49

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AlgoWatchlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instruments', models.CharField(max_length=100)),
                ('instrumentsToken', models.CharField(default='1111', max_length=100)),
                ('entryprice', models.FloatField(default=0.0)),
                ('lastTradedPrice', models.FloatField(default=0.0)),
                ('qty', models.IntegerField(default=1)),
                ('scaleup', models.IntegerField(default=1)),
                ('scaledown', models.IntegerField(default=1)),
                ('startAlgo', models.BooleanField(default=False, null=True)),
                ('algoStartTime', models.DateTimeField(null=True)),
                ('openPostion', models.BooleanField(default=False, null=True)),
                ('exchangeType', models.CharField(default='NFO', max_length=100)),
                ('segment', models.CharField(default='NFO-FUT', max_length=100)),
                ('instrumentType', models.CharField(default='CE', max_length=100)),
                ('slHitCount', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='DateTimeCheck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dateCheck', models.DateField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Instruments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instrument_token', models.CharField(max_length=100)),
                ('exchange_token', models.CharField(max_length=100)),
                ('tradingsymbol', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=100)),
                ('last_price', models.FloatField(default=0.0)),
                ('expiry', models.CharField(max_length=100)),
                ('tick_size', models.FloatField(default=0.0)),
                ('strike', models.FloatField(default=0.0)),
                ('lot_size', models.IntegerField(default=1)),
                ('instrument_type', models.CharField(max_length=100)),
                ('segment', models.CharField(max_length=100)),
                ('exchange', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ManualWatchlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instruments', models.CharField(max_length=100)),
                ('instrumentsToken', models.CharField(default='1111', max_length=100)),
                ('entryprice', models.FloatField(default=0.0)),
                ('lastTradedPrice', models.FloatField(default=0.0)),
                ('qty', models.IntegerField(default=1)),
                ('scaleup', models.IntegerField(default=1)),
                ('scaledown', models.IntegerField(default=1)),
                ('startAlgo', models.BooleanField(default=False, null=True)),
                ('algoStartTime', models.DateTimeField(null=True)),
                ('openPostion', models.BooleanField(default=False, null=True)),
                ('positionType', models.CharField(default='BUY', max_length=100)),
                ('exchangeType', models.CharField(default='NFO', max_length=100)),
                ('segment', models.CharField(default='NFO-FUT', max_length=100)),
                ('instrumentType', models.CharField(default='CE', max_length=100)),
                ('isBuyClicked', models.BooleanField(default=False)),
                ('isSellClicked', models.BooleanField(default=False)),
                ('slHitCount', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Orders',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instruments', models.CharField(max_length=100)),
                ('instrumentsToken', models.CharField(default='1111', max_length=100)),
                ('status', models.CharField(default='COMPLETE', max_length=100)),
                ('statusMessage', models.CharField(default='COMPLETE', max_length=100)),
                ('qty', models.IntegerField(default=1)),
                ('orderId', models.CharField(default='1111', max_length=100)),
                ('orderTimestamp', models.CharField(default='2021-05-31 09:18:57', max_length=100)),
                ('orderType', models.CharField(default='LIMIT', max_length=100)),
                ('transactionType', models.CharField(default='BUY', max_length=100)),
                ('avgTradedPrice', models.FloatField(default=0.0)),
                ('product', models.CharField(default='MIS', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Positions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instruments', models.CharField(max_length=100)),
                ('instrumentsToken', models.CharField(default='1111', max_length=100)),
                ('qty', models.IntegerField(default=1)),
                ('entryprice', models.FloatField(default=0.0)),
                ('avgTradedPrice', models.FloatField(default=0.0)),
                ('lastTradedPrice', models.FloatField(default=0.0)),
                ('pnl', models.FloatField(default=0.0)),
                ('unrealised', models.FloatField(default=0.0)),
                ('realised', models.FloatField(default=0.0)),
                ('startAlgo', models.BooleanField(default=False, null=True)),
                ('slPrice', models.FloatField(default=0.0)),
                ('tgPrice', models.FloatField(default=0.0)),
                ('orderId', models.CharField(default='1111', max_length=100)),
                ('positionType', models.CharField(default='', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Preferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.TimeField(default=datetime.time(10, 0))),
                ('stoploss', models.FloatField(default=0.2)),
                ('target', models.FloatField(default=1.0)),
                ('scaleupqty', models.IntegerField(default=1, null=True)),
                ('scaledownqty', models.IntegerField(default=1, null=True)),
                ('openingrange', models.FloatField(default=10.0, null=True)),
                ('openingrangebox', models.BooleanField(default=False, null=True)),
                ('scriptName', models.CharField(default='Default', max_length=100)),
            ],
        ),
    ]
