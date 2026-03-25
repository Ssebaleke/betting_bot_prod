from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscription", "0002_alter_subscription_end_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="reminder_sent",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="subscription",
            name="expiry_notified",
            field=models.BooleanField(default=False),
        ),
    ]
