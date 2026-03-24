from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0005_remove_smsconfig_sender_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="SMSBalance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("credits", models.PositiveIntegerField(default=0)),
                ("price_per_sms", models.DecimalField(decimal_places=2, default=0, help_text="Price per SMS charged to owner (UGX). Set by developers.", max_digits=8)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "SMS Balance"},
        ),
        migrations.CreateModel(
            name="SMSTopUp",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(max_length=20)),
                ("amount_paid", models.DecimalField(decimal_places=2, max_digits=10)),
                ("credits_added", models.PositiveIntegerField(default=0)),
                ("payment_reference", models.CharField(max_length=100, unique=True)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("SUCCESS", "Success"), ("FAILED", "Failed")], default="PENDING", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "SMS Top-Up", "ordering": ["-created_at"]},
        ),
    ]
