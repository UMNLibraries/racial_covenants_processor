from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import serializers, viewsets
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from django_filters import filters, FilterSet

from .models import CovenantedParcel, ShpExport, GeoJSONExport, CSVExport


# Serializers define the API representation.
class CovenantedParcelNoGeoSerializer(serializers.ModelSerializer):

    class Meta:
        model = CovenantedParcel
        exclude = ['geom_4326']


class CovenantedParcelGeoSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = CovenantedParcel
        fields = '__all__'
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


class CovenantFilter(FilterSet):
    min_deed_date = filters.IsoDateTimeFilter(field_name="deed_date", lookup_expr='gte')
    min_exec_date = filters.IsoDateTimeFilter(field_name="exec_date", lookup_expr='gte')
    max_deed_date = filters.IsoDateTimeFilter(field_name="deed_date", lookup_expr='lte')
    max_exec_date = filters.IsoDateTimeFilter(field_name="exec_date", lookup_expr='lte')
    county = filters.CharFilter(field_name='cnty_name', lookup_expr='iexact')

    class Meta:
        model = CovenantedParcel
        fields = ['workflow', 'workflow__workflow_name', 'state']


# ViewSets define the view behavior.
class CovenantNoGeoViewSet(viewsets.ModelViewSet):
    queryset = CovenantedParcel.objects.all()
    serializer_class = CovenantedParcelNoGeoSerializer
    filterset_class = CovenantFilter

    @method_decorator(cache_page(60*60*1))
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)


class CovenantGeoViewSet(viewsets.ModelViewSet):
    queryset = CovenantedParcel.objects.all()
    serializer_class = CovenantedParcelGeoSerializer
    filterset_class = CovenantFilter

    @method_decorator(cache_page(60*60*1))
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)


class ShpExportViewSet(viewsets.ModelViewSet):
    queryset = ShpExport.objects.all()
    serializer_class = ShpExportSerializer
    filterset_fields = ['workflow__workflow_name']


class GeoJSONExportViewSet(viewsets.ModelViewSet):
    queryset = GeoJSONExport.objects.all()
    serializer_class = GeoJSONExportSerializer
    filterset_fields = ['workflow__workflow_name']


class CSVExportViewSet(viewsets.ModelViewSet):
    queryset = CSVExport.objects.all()
    serializer_class = CSVExportSerializer
    filterset_fields = ['workflow__workflow_name']
