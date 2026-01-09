from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from apps.deed.models import DeedPage


@registry.register_document
class DeedPageDocument(Document):
    workflow = fields.NestedField(properties={
        'zoon_id': fields.IntegerField(),
        'workflow_name': fields.TextField(),
        'version': fields.TextField(),
        'slug': fields.TextField(),
    })

    matched_terms = fields.NestedField(properties={
        'term': fields.TextField(),
    })

    class Index:
        name = "deed_pages"
    class Django:
        model = DeedPage
        fields = [
            "page_ocr_text",
            "doc_num",
            "book_id",
            "page_num",
            "doc_date",
            "doc_type",
            "bool_match",
            "bool_exception",
        ]

        auto_refresh = True
        
        # Paginate the django queryset used to populate the index with the specified size
        # (by default it uses the database driver's default setting)
        queryset_pagination = 100
