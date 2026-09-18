import gzip
import json
import os

from django.conf import settings
from django.core.files.base import ContentFile


def compress_search_index(index):
    """Gzip the index JSON.

    Nothing in the stack gzips this for us -- no AWS_IS_GZIPPED, and S3 serves
    what it is given -- so the file is stored compressed and the browser
    inflates it with DecompressionStream.
    """
    payload = json.dumps(index, separators=(",", ":")).encode("utf-8")
    return gzip.compress(payload, compresslevel=9), len(payload)


def save_search_index_local(index, version_slug):
    out_dir = os.path.join(settings.BASE_DIR, "data", "main_exports", version_slug)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{version_slug}.json.gz")

    compressed, _raw_size = compress_search_index(index)
    with open(out_path, "wb") as f:
        f.write(compressed)

    return out_path


def save_search_index_export(index, workflow, version_slug, created_at):
    from apps.parcel.models import ParcelSearchIndex

    compressed, _raw_size = compress_search_index(index)

    export_obj = ParcelSearchIndex(
        workflow=workflow,
        parcel_count=len(index["parcels"]),
        created_at=created_at,
    )
    export_obj.index_file.save(
        f"{version_slug}.json.gz", ContentFile(compressed), save=False
    )
    export_obj.save()

    return export_obj
