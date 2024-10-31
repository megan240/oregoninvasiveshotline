from django.contrib import admin
from django.contrib.gis.admin.options import OSMGeoAdmin

from .models import Report


class CustomGeoModelAdmin(OSMGeoAdmin):
    list_display = ['report_id', '__str__',
                    'county', 'city',
                    'claimed_by', 'created_on']
    list_display_links = ['__str__']
    list_filter = ['has_specimen',
                   'county', 'city',
                   'edrr_status',
                   'is_archived', 'is_public',
                   'actual_species']


admin.site.register(Report, CustomGeoModelAdmin)
