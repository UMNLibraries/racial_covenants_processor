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

from apps.zoon import views
from apps.zoon.serializers import CovenantNoGeoViewSet, CovenantGeoViewSet

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'covenants', CovenantNoGeoViewSet)
router.register(r'covenants-geo', CovenantGeoViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('workflow/<int:workflow_id>/', views.workflow_summary, name='workflow'),
    path('workflow/<int:workflow_id>/matches/', views.covenant_matches, name='workflow_matches'),
    path('', views.index, name='index'),

    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls'))
]
