from rest_framework import serializers

from .models import DeedPage
from apps.zoon.models import ZooniverseWorkflow


class WorkflowSerializer(serializers.ModelSerializer):
    """Nested serializer for workflow details"""
    class Meta:
        model = ZooniverseWorkflow
        fields = ['id', 'zoon_id', 'workflow_name', 'version', 'slug']


# Serializers define the API representation.
class DeedPageSerializer(serializers.ModelSerializer):
    workflow = WorkflowSerializer(read_only=True)
    
    class Meta:
        model = DeedPage
        fields = [
            's3_lookup',
            'thumbnail_preview',
            'workflow',
            'record_link',
            'bool_match',
        ]