from rest_framework import serializers, viewsets
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import ZooniverseSubject


# Serializers define the API representation.
class CovenantNoGeoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZooniverseSubject
        fields = [
            'workflow',
            'bool_covenant_final',
            'zoon_subject_id',
            'covenant_text_final',
            'deed_date_final',
            'seller_final',
            'buyer_final',
            'bool_parcel_match',
            'join_candidates',
            'match_type',
            'median_score',
            'bool_manual_correction',
            'addition_final',
            'lot_final',
            'block_final',
            'match_type_final',
            'date_updated',
        ]


class CovenantGeoSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = ZooniverseSubject

        fields = [
            'workflow',
            'bool_covenant_final',
            'zoon_subject_id',
            'covenant_text_final',
            'deed_date_final',
            'seller_final',
            'buyer_final',
            'bool_parcel_match',
            'join_candidates',
            'match_type',
            'median_score',
            'bool_manual_correction',
            'addition_final',
            'lot_final',
            'block_final',
            'match_type_final',
            'date_updated',
        ]

        geo_field = 'geom_union_4326'

# ViewSets define the view behavior.
class CovenantNoGeoViewSet(viewsets.ModelViewSet):
    queryset = ZooniverseSubject.objects.filter(bool_covenant_final=True)
    serializer_class = CovenantNoGeoSerializer


class CovenantGeoViewSet(viewsets.ModelViewSet):
    queryset = ZooniverseSubject.objects.filter(bool_covenant_final=True, bool_parcel_match=True)
    serializer_class = CovenantGeoSerializer
