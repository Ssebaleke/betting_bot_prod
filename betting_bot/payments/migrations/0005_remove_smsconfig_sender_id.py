from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0004_smsconfig"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="smsconfig",
            name="sender_id",
        ),
    ]
