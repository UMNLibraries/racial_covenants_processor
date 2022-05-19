from django.db.models import Prefetch

from rest_framework import serializers, viewsets
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Parcel
from apps.zoon.models import ZooniverseSubject


# Serializers define the API representation.
class ParcelNoGeoSerializer(serializers.ModelSerializer):
    covenant_text = serializers.CharField()
    zoon_subject_id = serializers.CharField()
    image_ids = serializers.CharField()
    zoon_dt_retired = serializers.DateTimeField()
    median_score = serializers.FloatField()
    manual_cx = serializers.BooleanField()
    addition_cov = serializers.CharField()
    lot_cov = serializers.CharField()
    block_cov = serializers.CharField()
    seller = serializers.CharField()
    buyer = serializers.CharField()
    deed_date = serializers.DateField()
    match_type = serializers.CharField()
    date_updated = serializers.DateTimeField()

    addition_modern = serializers.CharField(source='plat_name')
    block_modern = serializers.CharField(source='block')
    lot_modern = serializers.CharField(source='lot')
    phys_description_modern = serializers.CharField(source='phys_description')

    class Meta:
        model = Parcel
        fields = [
            'workflow',
            'county_name',
            'county_fips',

            'deed_date',
            'seller',
            'buyer',
            'covenant_text',

            'zoon_subject_id',
            'zoon_dt_retired',
            'image_ids',
            'median_score',
            'manual_cx',
            'match_type',

            'street_address',
            'city',
            'state',
            'zip_code',

            'addition_cov',
            'lot_cov',
            'block_cov',

            'pin_primary',
            'addition_modern',
            'block_modern',
            'lot_modern',
            'phys_description_modern',

            'plat',

            'date_updated',
        ]


class ParcelGeoSerializer(GeoFeatureModelSerializer):
    covenant_text = serializers.CharField()
    zoon_subject_id = serializers.CharField()
    image_ids = serializers.CharField()
    zoon_dt_retired = serializers.DateTimeField()
    median_score = serializers.FloatField()
    manual_cx = serializers.BooleanField()
    addition_cov = serializers.CharField()
    lot_cov = serializers.CharField()
    block_cov = serializers.CharField()
    seller = serializers.CharField()
    buyer = serializers.CharField()
    deed_date = serializers.DateField()
    match_type = serializers.CharField()
    date_updated = serializers.DateTimeField()

    addition_modern = serializers.CharField(source='plat_name')
    block_modern = serializers.CharField(source='block')
    lot_modern = serializers.CharField(source='lot')
    phys_description_modern = serializers.CharField(source='phys_description')

    class Meta:
        model = Parcel

        fields = [
            'workflow',
            'county_name',
            'county_fips',

            'deed_date',
            'seller',
            'buyer',
            'covenant_text',

            'zoon_subject_id',
            'zoon_dt_retired',
            'image_ids',
            'median_score',
            'manual_cx',
            'match_type',

            'street_address',
            'city',
            'state',
            'zip_code',

            'addition_cov',
            'lot_cov',
            'block_cov',

            'pin_primary',
            'addition_modern',
            'block_modern',
            'lot_modern',
            'phys_description_modern',

            'plat',

            'date_updated',
        ]

        geo_field = 'geom_4326'


# ViewSets define the view behavior.
class CovenantNoGeoViewSet(viewsets.ModelViewSet):
    queryset = Parcel.covenant_objects.all()
    serializer_class = ParcelNoGeoSerializer


class CovenantGeoViewSet(viewsets.ModelViewSet):
    queryset = Parcel.covenant_objects.all()
    serializer_class = ParcelGeoSerializer
