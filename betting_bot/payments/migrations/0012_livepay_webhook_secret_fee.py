from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0011_kwapay_provider'),
    ]

    operations = [
        migrations.AddField(
            model_name='livepayprovider',
            name='webhook_secret',
            field=models.CharField(
                blank=True, max_length=255,
                help_text='Webhook Secret from LivePay dashboard \u2192 Webhook Configuration'
            ),
        ),
        migrations.AddField(
            model_name='livepayprovider',
            name='gateway_fee_percentage',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('0.00'), max_digits=5,
                help_text='LivePay gateway fee % per transaction e.g. 3.0 for 3%'
            ),
        ),
    ]
