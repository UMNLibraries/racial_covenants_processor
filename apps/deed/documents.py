from django_opensearch_dsl import Document, fields
from django_opensearch_dsl.registries import registry

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

    def get_indexing_queryset(self, verbose=False, filter_=None, exclude=None,
                              alias=None, count=None, action=None, stdout=None):
        """Stream the indexing queryset using keyset (seek) pagination.

        django-opensearch-dsl's default ``get_indexing_queryset`` paginates with
        ``qs[i:i + chunk_size]`` (SQL OFFSET), which is O(offset) per chunk and so
        degrades quadratically when indexing millions of rows. Its
        ``Document.get_queryset`` also uses a plain ``model.objects.all()`` that
        bypasses the ``Django.get_queryset`` optimization, causing N+1 queries in
        ``prepare_workflow`` / ``prepare_matched_terms``.

        This override fixes both: it seeks by primary key (``pk > last_pk``,
        O(chunk_size) via the PK index, so throughput stays flat at any depth) over
        a queryset that ``select_related`` the workflow and ``prefetch_related`` the
        matched terms. ``--filter`` / ``--exclude`` are honored; ``--count`` (which
        applies a global LIMIT) falls back to the library default.
        """
        if count is not None:
            kwargs = {"verbose": verbose, "filter_": filter_, "exclude": exclude,
                      "alias": alias, "count": count}
            if action is not None:
                kwargs["action"] = action
            if stdout is not None:
                kwargs["stdout"] = stdout
            yield from super().get_indexing_queryset(**kwargs)
            return

        qs = self.django.model.objects
        if alias:
            qs = qs.using(alias)
        qs = qs.select_related("workflow").prefetch_related("matched_terms")
        if filter_:
            qs = qs.filter(filter_)
        if exclude:
            qs = qs.exclude(exclude)
        qs = qs.order_by("pk")

        chunk_size = self.django.queryset_pagination
        last_pk = None
        while True:
            chunk = list((qs.filter(pk__gt=last_pk) if last_pk is not None else qs)[:chunk_size])
            if not chunk:
                break
            yield from chunk
            last_pk = chunk[-1].pk

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
