from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0007_smslog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='provider_type',
            field=models.CharField(
                choices=[
                    ('MAKYPAY', 'MakyPay'),
                    ('YOO', 'Yo! Payments'),
                    ('LIVE', 'LivePay'),
                ],
                default='MAKYPAY',
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name='LivePayProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='LivePay', max_length=50)),
                ('public_key', models.CharField(max_length=255)),
                ('secret_key', models.CharField(max_length=255)),
                ('transaction_pin', models.CharField(blank=True, help_text='PIN for Send Money (withdrawals)', max_length=20)),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'LivePay Provider'},
        ),
        migrations.CreateModel(
            name='RevenueConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentage', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Platform revenue % deducted from each successful payment (e.g. 10 = 10%)', max_digits=5)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Revenue Config'},
        ),
        migrations.CreateModel(
            name='OwnerWallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('total_earned', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Owner Wallet'},
        ),
        migrations.CreateModel(
            name='WithdrawalRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payout_phone', models.CharField(max_length=20)),
                ('payout_network', models.CharField(choices=[('MTN', 'MTN Mobile Money'), ('AIRTEL', 'Airtel Money')], default='MTN', max_length=10)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PAID', 'Paid'), ('FAILED', 'Failed')], default='PENDING', max_length=10)),
                ('failure_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Withdrawal Request', 'ordering': ['-created_at']},
        ),
    ]
