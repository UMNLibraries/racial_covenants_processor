from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from apps.deed.models import DeedPage


@registry.register_document
class DeedPageDocument(Document):
    # Identifier fields - use KeywordField for exact matches and filtering
    s3_lookup = fields.KeywordField()
    doc_num = fields.KeywordField()
    doc_alt_id = fields.KeywordField()
    book_id = fields.KeywordField()
    public_uuid = fields.KeywordField()
    
    # Numeric field
    page_num = fields.IntegerField()
    
    # Boolean field for filtering
    bool_match = fields.BooleanField()
    
    # Text field for full-text search
    doc_type = fields.TextField()
    
    workflow = fields.NestedField(properties={
        'zoon_id': fields.IntegerField(),
        'workflow_name': fields.TextField(),
    })

    matched_terms = fields.NestedField(properties={
        'term': fields.TextField(),
    })

    def prepare_workflow(self, instance):
        """Extract workflow data, using the select_related optimization."""
        if instance.workflow:
            return {
                'zoon_id': instance.workflow.zoon_id,
                'workflow_name': instance.workflow.workflow_name,
            }
        return None

    def prepare_matched_terms(self, instance):
        """Extract matched terms, using the prefetch_related optimization."""
        # This uses the prefetched data from get_queryset()
        return [{'term': term.term} for term in instance.matched_terms.all()]

    class Index:
        name = "deed_pages"
    class Django:
        model = DeedPage
        # All fields are explicitly defined as class attributes above

        # Assuming that during batch indexing, we do not need to make documents available immediately.
        # Auto refresh slows down batch indexing.
        auto_refresh = False
        
        # The number of objects to query in a batch and process during indexing
        # We might have to play with this value to balance indexing time and memory usage
        # (larger value means fewer queries, but more memory usage)
        queryset_pagination = 500

        def get_queryset(self):
            """Optimize queryset to avoid N+1 queries during indexing."""
            return (
                self.model.objects
                .select_related('workflow')  # Optimize ForeignKey access
                .prefetch_related('matched_terms')  # Optimize ManyToMany access
                .only(
                    'workflow',
                    's3_lookup',
                    'doc_num',
                    'doc_alt_id',
                    'book_id',
                    'page_num',
                    'doc_type',
                    'public_uuid',
                    'bool_match',
                )
            )
