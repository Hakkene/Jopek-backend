# Generated by Django 4.1.2 on 2022-11-17 03:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0018_alter_product_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rentproduct',
            name='renteduntill',
        ),
    ]
