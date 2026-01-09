"""racial_covenants_processor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

from apps.zoon import views
from apps.zoon.serializers import SubjectNoGeoViewSet, SubjectGeoViewSet
from apps.parcel.serializers import CovenantNoGeoViewSet, CovenantGeoViewSet, ShpExportViewSet, GeoJSONExportViewSet, CSVExportViewSet

from apps.deed.views import DeedPageViewSet, deed_search_page

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'subjects', SubjectNoGeoViewSet)
router.register(r'subjects-geo', SubjectGeoViewSet, basename='subjectsgeo')

router.register(r'covenants', CovenantNoGeoViewSet)
router.register(r'covenants-geo', CovenantGeoViewSet, basename='covenantsgeo')

router.register(r'shp-exports', ShpExportViewSet)
router.register(r'geojson-exports', GeoJSONExportViewSet)
router.register(r'csv-exports', CSVExportViewSet)
router.register(r'deeds', DeedPageViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('workflow/<int:workflow_id>/', views.workflow_summary, name='workflow'),
    path('workflow/<int:workflow_id>/matches/', views.covenant_matches, name='workflow_matches'),

    path('workflow/<str:workflow_slug>/', views.workflow_summary_slug, name='workflow_slug'),

    path('zooniverse-subject-lookup/<int:zoon_subject_id>/', views.zoon_subject_lookup, name='zoon_subject_lookup'),

    path('', views.index, name='index'),

    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),

    path("deed_search/", deed_search_page, name="deed_search_view"),

    # path('__debug__/', include('debug_toolbar.urls')),
]

if settings.DEBUG_TOOLBAR_ON:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()

urlpatterns += staticfiles_urlpatterns()