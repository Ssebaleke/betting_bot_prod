import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('packages', '0003_packagecategory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Prediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home_team', models.CharField(max_length=100)),
                ('away_team', models.CharField(max_length=100)),
                ('prediction', models.CharField(help_text='e.g. Arsenal to win, Over 2.5, BTTS Yes', max_length=100)),
                ('odds', models.DecimalField(decimal_places=2, max_digits=6)),
                ('match_time', models.TimeField(help_text='Match kick-off time')),
                ('match_date', models.DateField(help_text='Date match is played')),
                ('send_date', models.DateField(default=django.utils.timezone.now, help_text='Date to send this prediction to subscribers (can be before match day)')),
                ('send_time', models.TimeField(default='08:00', help_text='Time to send this prediction to subscribers')),
                ('package', models.ForeignKey(help_text='Which package receives this prediction', on_delete=django.db.models.deletion.CASCADE, to='packages.package')),
                ('is_active', models.BooleanField(default=True)),
                ('is_sent', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('send_date', 'match_time'),
            },
        ),
        migrations.CreateModel(
            name='PredictionDelivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('send_date', models.DateField()),
                ('delivered_at', models.DateTimeField(auto_now_add=True)),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='packages.package')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'send_date', 'package')},
            },
        ),
    ]
