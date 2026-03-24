from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("packages", "0002_alter_package_options_package_level_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PackageCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="e.g. Daily, Weekly, Monthly", max_length=50, unique=True)),
                ("description", models.TextField(blank=True, help_text="Short description of this category")),
                ("is_active", models.BooleanField(default=True, help_text="Disable to hide this category")),
                ("order", models.PositiveIntegerField(default=1, help_text="Display order (lower = first)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Package Category",
                "verbose_name_plural": "Package Categories",
                "ordering": ["order"],
            },
        ),
        migrations.AddField(
            model_name="package",
            name="category",
            field=models.ForeignKey(
                blank=True,
                help_text="Category this package belongs to (e.g. Daily, Weekly)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="packages",
                to="packages.packagecategory",
            ),
        ),
    ]
