from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0010_platformwallet'),
    ]

    operations = [
        migrations.CreateModel(
            name='KwaPayProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='KwaPay', max_length=50)),
                ('primary_api', models.CharField(max_length=255)),
                ('secondary_api', models.CharField(max_length=255)),
                ('callback_url', models.URLField(help_text='Webhook URL KwaPay will POST results to')),
                ('withdrawal_fee', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Fixed fee deducted from every withdrawal (UGX).', max_digits=10)),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'KwaPay Provider'},
        ),
        migrations.AlterField(
            model_name='payment',
            name='provider_type',
            field=models.CharField(
                choices=[
                    ('MAKYPAY', 'MakyPay'),
                    ('YOO', 'Yo! Payments'),
                    ('LIVE', 'LivePay'),
                    ('KWA', 'KwaPay'),
                ],
                default='MAKYPAY',
                max_length=10,
            ),
        ),
    ]
