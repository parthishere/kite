"""kitetrades URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.schemas import get_schema_view
from rest_framework.documentation import include_docs_urls


admin.site.site_header = "OpenAlgo Admin"
admin.site.site_title = "OpenAlgo Admin Portal"
admin.site.index_title = "Welcome to OpenAlgo Portal"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('playground.urls')),
    path("api/", include('playground.api.urls')),
    path('schema/', get_schema_view(
        title="API",
        description="API for the Trading App",
        version="1.0.0"
    ), name="social-schema"),
    path('api/', include_docs_urls(
        title="API",
        description="API for the Trading App",
    ), name="social-docs")
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
