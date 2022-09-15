from rest_framework import serializers, viewsets
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Parcel, ShpExport, GeoJSONExport, CSVExport
from apps.zoon.models import ZooniverseSubject

covenant_api_fields = [
    'workflow',
    'cnty_name',
    'cnty_fips',

    'deed_date',
    'seller',
    'buyer',
    'cov_type',
    'cov_text',

    'zn_subj_id',
    'zn_dt_ret',
    'image_ids',
    'med_score',
    'manual_cx',
    'match_type',

    'street_add',
    'city',
    'state',
    'zip_code',

    'add_cov',
    'lot_cov',
    'block_cov',

    'cnty_pin',
    'add_mod',
    'block_mod',
    'lot_mod',
    'ph_dsc_mod',

    'plat',

    'dt_updated',
]

# Serializers define the API representation.
class ParcelNoGeoSerializer(serializers.ModelSerializer):
    # mostly defined in annotations on model manager in  models.py
    cov_type = serializers.CharField()
    cov_text = serializers.CharField()
    zn_subj_id = serializers.CharField()
    image_ids = serializers.CharField()
    zn_dt_ret = serializers.DateTimeField()
    med_score = serializers.FloatField()
    manual_cx = serializers.BooleanField()
    add_cov = serializers.CharField()
    block_cov = serializers.CharField()
    lot_cov = serializers.CharField()
    seller = serializers.CharField()
    buyer = serializers.CharField()
    deed_date = serializers.DateField()
    match_type = serializers.CharField()
    dt_updated = serializers.DateTimeField()
    cnty_name = serializers.CharField()
    cnty_fips = serializers.CharField()
    cnty_pin = serializers.CharField()
    street_add= serializers.CharField()
    add_mod = serializers.CharField()
    block_mod = serializers.CharField()
    lot_mod = serializers.CharField()
    ph_dsc_mod = serializers.CharField()

    class Meta:
        model = Parcel
        fields = covenant_api_fields


class ParcelGeoSerializer(GeoFeatureModelSerializer):
    # mostly defined in annotations on model manager in  models.py
    cov_type = serializers.CharField()
    cov_text = serializers.CharField()
    zn_subj_id = serializers.CharField()
    image_ids = serializers.CharField()
    zn_dt_ret = serializers.DateTimeField()
    med_score = serializers.FloatField()
    manual_cx = serializers.BooleanField()
    add_cov = serializers.CharField()
    block_cov = serializers.CharField()
    lot_cov = serializers.CharField()
    seller = serializers.CharField()
    buyer = serializers.CharField()
    deed_date = serializers.DateField()
    match_type = serializers.CharField()
    dt_updated = serializers.DateTimeField()
    cnty_name = serializers.CharField()
    cnty_fips = serializers.CharField()
    cnty_pin = serializers.CharField()
    street_add= serializers.CharField()
    add_mod = serializers.CharField()
    block_mod = serializers.CharField()
    lot_mod = serializers.CharField()
    ph_dsc_mod = serializers.CharField()

    class Meta:
        model = Parcel

        fields = covenant_api_fields

        geo_field = 'geom_4326'


class ShpExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShpExport

        fields = '__all__'


class GeoJSONExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoJSONExport

        fields = '__all__'


class CSVExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVExport

        fields = '__all__'


# ViewSets define the view behavior.
class CovenantNoGeoViewSet(viewsets.ModelViewSet):
    queryset = Parcel.covenant_objects.all()
    serializer_class = ParcelNoGeoSerializer


class CovenantGeoViewSet(viewsets.ModelViewSet):
    queryset = Parcel.covenant_objects.all()
    serializer_class = ParcelGeoSerializer


class ShpExportViewSet(viewsets.ModelViewSet):
    queryset = ShpExport.objects.all()
    serializer_class = ShpExportSerializer


class GeoJSONExportViewSet(viewsets.ModelViewSet):
    queryset = GeoJSONExport.objects.all()
    serializer_class = GeoJSONExportSerializer


class CSVExportViewSet(viewsets.ModelViewSet):
    queryset = CSVExport.objects.all()
    serializer_class = CSVExportSerializer
