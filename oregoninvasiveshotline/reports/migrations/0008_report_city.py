from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('cities', '0001_initial'),
        ('reports', '0007_change_default_ordering'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='city',
            field=models.ForeignKey(null=True, to='cities.City', on_delete=django.db.models.deletion.SET_NULL),
        ),
    ]