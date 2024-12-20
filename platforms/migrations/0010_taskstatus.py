# Generated by Django 5.0.7 on 2024-11-19 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platforms', '0009_playstoreproduct_sessionid_playstoreproduct_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='taskStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sessionId', models.CharField(max_length=100)),
                ('user', models.CharField(max_length=100)),
                ('completed', models.BooleanField(default=False)),
                ('status', models.CharField(default='Pending', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
