from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscription", "0003_subscription_reminder_sent"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="expiry_notified",
            field=models.BooleanField(default=False),
        ),
    ]
