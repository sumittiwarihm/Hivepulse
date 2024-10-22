# Generated by Django 5.0.7 on 2024-08-27 07:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='amazonProduct',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('Asin', models.CharField(max_length=50)),
                ('Brand', models.CharField(max_length=500)),
                ('Status', models.CharField(default='pending', max_length=50)),
                ('Date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='flipkartProduct',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('Fsn', models.CharField(max_length=50)),
                ('Brand', models.CharField(max_length=500)),
                ('Status', models.CharField(default='pending', max_length=50)),
                ('Date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='playstoreProduct',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('AppId', models.CharField(max_length=50)),
                ('Brand', models.CharField(max_length=500)),
                ('Status', models.CharField(default='pending', max_length=50)),
                ('Date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='review',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('reviewContent', models.TextField()),
                ('rating', models.IntegerField()),
                ('created_at', models.DateField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
        ),
        migrations.CreateModel(
            name='sentimentResult',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('positiveScore', models.FloatField(default=0)),
                ('neutralScore', models.FloatField(default=0)),
                ('negativeScore', models.FloatField(default=0)),
                ('estimatedResult', models.CharField(default='', max_length=50)),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='platforms.review')),
            ],
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['content_type', 'object_id'], name='platforms_r_content_c00864_idx'),
        ),
    ]