import copy
from abc import abstractmethod

from elasticsearch_dsl import Document, Q
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import render
from django.db.models import Case, When

from .documents import DeedPageDocument
from .serializers import DeedPageSerializer
from .models import DeedPage
from .forms import DeedSearchForm

class PaginatedElasticSearchAPIView(ModelViewSet, LimitOffsetPagination):
    document_class: Document = None

    @abstractmethod
    def generate_search_query(self, search_terms_list, param_filters):
        """This method should be overridden
        and return a Q() expression."""

    @action(methods=["GET"], detail=False, url_path="search")
    def search(self, request: Request):
        try:
            params = copy.deepcopy(request.query_params)

            raw_search = params.pop("search", None)
            search_terms = raw_search if isinstance(raw_search, list) else [raw_search] if raw_search else None

            query = self.generate_search_query(
                search_terms_list=search_terms, param_filters=params
            )

            search = self.document_class.search().query(query)

            # Get pagination bounds
            limit = int(request.query_params.get("limit", 10))
            offset = int(request.query_params.get("offset", 0))

            # Slice the Search object BEFORE execution
            paginated_search = search[offset:offset + limit]

            # Execute the paginated search
            response = paginated_search.execute()

            total = (
                response.hits.total.value
                if hasattr(response.hits.total, "value")
                else response.hits.total
            )

            # --------------------
            # STEP 1: Extract IDs
            # --------------------
            ids = [hit.meta.id for hit in response.hits]

            if not ids:
                return Response({
                    "count": 0,
                    "results": [],
                })

            # --------------------
            # STEP 2: Hydrate from DB
            # --------------------
            qs = DeedPage.objects.filter(id__in=ids).select_related('workflow')

            # Preserve ES ordering
            order = Case(
                *[When(id=pk, then=pos) for pos, pk in enumerate(ids)]
            )
            qs = qs.order_by(order)

            # --------------------
            # STEP 3: Serialize
            # --------------------
            serializer = self.serializer_class(qs, many=True)

            next_offset = offset + limit if offset + limit < total else None
            previous_offset = offset - limit if offset - limit >= 0 else None

            return Response({
                "count": total,
                "limit": limit,
                "offset": offset,
                "next": next_offset,
                "previous": previous_offset,
                "results": serializer.data,
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class DeedPageViewSet(PaginatedElasticSearchAPIView):
    serializer_class = DeedPageSerializer
    queryset = DeedPage.objects.all()
    document_class = DeedPageDocument

    def generate_search_query(self, search_terms_list: list[str], param_filters: dict):
        if search_terms_list is None:
            return Q("match_all")
        
        search_terms = search_terms_list[0].replace("\x00", "")
        search_terms = search_terms.replace(",", " ")
        
        # Check if search term is numeric
        is_numeric = search_terms.strip().isdigit()
        
        # Separate fields by type
        keyword_fields = [
            "s3_lookup",
            "doc_num",
            "doc_alt_id",
            "book_id",
            "public_uuid",
        ]
        
        text_fields = [
            "doc_type",
        ]
        
        numeric_fields = [
            "page_num",
        ]
        
        # Build queries for different field types
        queries = []
        
        # Text field query (only doc_type)
        if text_fields:
            queries.append(Q(
                "multi_match",
                query=search_terms,
                fields=text_fields,
                fuzziness="auto",
                minimum_should_match="70%"
            ))
        
        # Keyword field queries (wildcard for partial matches)
        keyword_queries = [
            Q("wildcard", **{field: f"*{search_terms.lower()}*"}) 
            for field in keyword_fields
        ]
        if keyword_queries:
            queries.append(Q("bool", should=keyword_queries, minimum_should_match=1))
        
        # Nested field queries
        # Workflow nested query
        queries.append(Q(
            "nested",
            path="workflow",
            query=Q("match", **{"workflow.workflow_name": search_terms})
        ))
        
        # Matched terms nested query
        queries.append(Q(
            "nested",
            path="matched_terms",
            query=Q("match", **{"matched_terms.term": search_terms})
        ))
        
        # Numeric field query (if numeric search)
        if is_numeric:
            queries.append(Q(
                "multi_match",
                query=search_terms,
                fields=numeric_fields
            ))
        
        # Combine all queries with OR
        if queries:
            query = queries[0]
            for q in queries[1:]:
                query = query | q
            return query
        
        return Q("match_all")
    

def deed_search_page(request):
    form = DeedSearchForm(request.GET or None)
    return render(
        request, 
        "search/search.html", 
        {
            "form": form,
        }
    )