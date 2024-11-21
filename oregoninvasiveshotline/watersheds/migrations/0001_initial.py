from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Watershed',
            fields=[
                ('watershed_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('state', models.CharField(max_length=255)),
                ('the_geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
            ],
            options={
                'db_table': 'watershed',
                'ordering': ['state', 'name'],
            },
        ),
    ]