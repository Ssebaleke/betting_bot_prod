from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0003_payment_delivery_channel"),
    ]

    operations = [
        migrations.CreateModel(
            name="SMSConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("api_key", models.CharField(help_text="UGSMS v2 API Key", max_length=255)),
                ("sender_id", models.CharField(default="BetTips", help_text="Sender name shown on SMS", max_length=20)),
                ("is_active", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "SMS Config (UGSMS)"},
        ),
    ]
