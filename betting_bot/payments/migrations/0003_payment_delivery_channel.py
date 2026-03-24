from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_yoopaymentprovider"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="delivery_channel",
            field=models.CharField(
                choices=[("TELEGRAM", "Telegram"), ("SMS", "SMS")],
                default="TELEGRAM",
                max_length=10,
            ),
        ),
    ]
