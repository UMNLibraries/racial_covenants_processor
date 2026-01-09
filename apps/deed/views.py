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

        text_search_fields = [
            "page_ocr_text",
            "doc_num",
            "doc_type",
            "matched_terms",
            "workflow",
            "book_id",
        ]
        numeric_fields = [
            "page_num",
        ]
        filter_fields = [
            "bool_match",
            "bool_exception",
            "doc_date",
        ]

        fuzzy_query = Q(
            "multi_match",
            query=search_terms,
            fields=text_search_fields,
            fuzziness="auto",
            minimum_should_match="70%"
        )
        
        # Only create exact_query for numeric searches to avoid parsing errors
        if is_numeric:
            exact_query = Q(
                "multi_match",
                query=search_terms,
                fields=numeric_fields
            )
        else:
            exact_query = None
            
        wildcard_query = Q(
            "bool",
            should=[
                Q("wildcard", **{field: f"*{search_terms.lower()}*"}) 
                for field in text_search_fields
            ],
        )

        # Conditionally combine queries based on whether search is numeric
        if is_numeric:
            query = fuzzy_query | exact_query | wildcard_query
        else:
            query = fuzzy_query | wildcard_query

        if len(param_filters) > 0:
            filters = []
            for field in filter_fields:
                if field in param_filters:
                    filters.append(Q("term", **{field: param_filters[field]}))
            filter_query = Q("bool", should=[query], filter=filters)
            query = query & filter_query

        return query
    

def deed_search_page(request):
    form = DeedSearchForm(request.GET or None)
    return render(
        request, 
        "search/search.html", 
        {
            "form": form,
        }
    )