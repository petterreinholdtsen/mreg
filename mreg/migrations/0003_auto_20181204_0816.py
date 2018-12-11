# Generated by Django 2.1.3 on 2018-12-04 07:16

from django.db import migrations, models
import mreg.validators


class Migration(migrations.Migration):

    dependencies = [
        ('mreg', '0002_auto_20181203_1213'),
    ]

    operations = [
        migrations.RenameField(
            model_name='srv',
            old_name='service',
            new_name='name',
        ),
        migrations.AlterField(
            model_name='naptr',
            name='orderv',
            field=models.IntegerField(default=0, validators=[mreg.validators.validate_16bit_uint]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='naptr',
            name='preference',
            field=models.IntegerField(default=0, validators=[mreg.validators.validate_16bit_uint]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='srv',
            name='port',
            field=models.IntegerField(default=0, validators=[mreg.validators.validate_16bit_uint]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='srv',
            name='priority',
            field=models.IntegerField(default=0, validators=[mreg.validators.validate_16bit_uint]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='srv',
            name='weight',
            field=models.IntegerField(default=0, validators=[mreg.validators.validate_16bit_uint]),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='srv',
            unique_together={('name', 'priority', 'weight', 'port', 'target')},
        ),
    ]