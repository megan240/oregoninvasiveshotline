from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('watersheds', '0001_initial'),
        ('reports', '0008_report_city'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='watershed',
            field=models.ForeignKey(null=True, to='watersheds.Watershed', on_delete=django.db.models.deletion.SET_NULL),
        ),
    ]
