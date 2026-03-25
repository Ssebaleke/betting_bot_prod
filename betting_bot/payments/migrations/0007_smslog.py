from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0006_smsbalance_smstopup"),
    ]

    operations = [
        migrations.CreateModel(
            name="SMSLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(max_length=20)),
                ("message", models.TextField()),
                ("status", models.CharField(choices=[("SENT", "Sent"), ("FAILED", "Failed")], max_length=10)),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "SMS Log", "ordering": ["-sent_at"]},
        ),
    ]
