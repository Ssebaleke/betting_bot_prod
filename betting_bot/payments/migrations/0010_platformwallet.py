from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0009_livepay_withdrawal_fee'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformWallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_earned', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Platform Wallet (Super Admin)',
            },
        ),
    ]
