from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='YooPaymentProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Yo! Payments', max_length=50)),
                ('api_username', models.CharField(max_length=200)),
                ('api_password', models.CharField(max_length=200)),
                ('environment', models.CharField(choices=[('SANDBOX', 'Sandbox'), ('LIVE', 'Live')], default='LIVE', max_length=10)),
                ('is_active', models.BooleanField(default=False)),
                ('primary_url', models.URLField(default='https://paymentsapi1.yo.co.ug/ybs/task.php')),
                ('backup_url', models.URLField(default='https://paymentsapi2.yo.co.ug/ybs/task.php')),
                ('notification_url', models.URLField(help_text='IPN success webhook URL')),
                ('failure_url', models.URLField(help_text='IPN failure webhook URL')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Yo! Payment Provider'},
        ),
        migrations.AddField(
            model_name='payment',
            name='provider_type',
            field=models.CharField(
                choices=[('MAKYPAY', 'MakyPay'), ('YOO', 'Yo! Payments')],
                default='MAKYPAY',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='provider',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.PROTECT,
                to='payments.paymentprovider',
            ),
        ),
    ]
