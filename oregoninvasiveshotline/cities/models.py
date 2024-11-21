from django.contrib.gis.db import models


class City(models.Model):
    class Meta:
        db_table = 'city'
        ordering = ['state', 'name']

    city_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    the_geom = models.MultiPolygonField(srid=4326)
    
    @property
    def label(self):
        if self.state == 'Oregon':
            return self.name
        elif self.state == 'Washington':
            return f"{self.name}, WA"
        return f"{self.name}, {self.state}"

    def __str__(self):
        return self.label
