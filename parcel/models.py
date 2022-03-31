from django.contrib.gis.db import models


class Parcel(models.Model):
    geom = models.MultiPolygonField(srid=4326)

# Create your models here.
# https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip
