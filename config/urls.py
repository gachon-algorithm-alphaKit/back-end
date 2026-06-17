"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
import os
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import FileResponse, Http404
from django.conf import settings
from django.conf.urls.static import static

def flutter_serve(request, path):
    if '..' in path:
        raise Http404()
        
    full_path = os.path.join(settings.FLUTTER_WEB_DIR, path)
    
    if path and os.path.isfile(full_path):
        return FileResponse(open(full_path, 'rb'))
    
    index_path = os.path.join(settings.FLUTTER_WEB_DIR, 'index.html')
    if os.path.isfile(index_path):
        return FileResponse(open(index_path, 'rb'))
        
    raise Http404()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    re_path(r'^(?P<path>.*)$', flutter_serve),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
