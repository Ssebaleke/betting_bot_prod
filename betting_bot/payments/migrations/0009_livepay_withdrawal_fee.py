from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0008_livepay_revenue_wallet'),
    ]

    operations = [
        migrations.AddField(
            model_name='livepayprovider',
            name='withdrawal_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Fixed fee added on top of every withdrawal (UGX). Set manually.',
                max_digits=10,
            ),
        ),
    ]
