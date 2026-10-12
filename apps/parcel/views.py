import hmac
import re

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.parcel.models import PMTilesExport
from apps.zoon.models import ZooniverseWorkflow

PMTILES_KEY_RE = re.compile(r"^main_exports/[A-Za-z0-9_-]+\.pmtiles$")


class PMTilesCallbackView(APIView):
    """Called by the mp-covenants-pmtiles-export Lambda once it has uploaded a
    freshly baked .pmtiles to S3.

    Authenticated by a shared secret rather than a Django user.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        expected = settings.PMTILES_CALLBACK_TOKEN
        presented = request.headers.get("X-Callback-Token", "")
        if not expected or not hmac.compare_digest(presented, expected):
            return Response(status=status.HTTP_403_FORBIDDEN)

        pmtiles_key = request.data.get("pmtiles_key", "")
        if not isinstance(pmtiles_key, str) or not PMTILES_KEY_RE.match(pmtiles_key):
            return Response(
                {"detail": "Invalid pmtiles_key."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            workflow_id = int(request.data["workflow_id"])
            covenant_count = int(request.data["covenant_count"])
        except (KeyError, TypeError, ValueError):
            return Response(
                {"detail": "workflow_id and covenant_count are required integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            workflow = ZooniverseWorkflow.objects.get(pk=workflow_id)
        except ZooniverseWorkflow.DoesNotExist:
            return Response(
                {"detail": "No such workflow."}, status=status.HTTP_404_NOT_FOUND
            )

        export, created = PMTilesExport.objects.get_or_create(
            workflow=workflow,
            pmtiles=pmtiles_key,
            defaults={
                "covenant_count": covenant_count,
                "created_at": timezone.now(),
            },
        )

        return Response(
            {"id": export.pk, "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
