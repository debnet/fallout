# coding: utf-8
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.authtoken import views as drf_views

from fallout.urls import urlpatterns as fallout_urls, api_urlpatterns as fallout_api


admin.site.site_header = 'Fallout RPG'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='fallout/login.html')),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    # Django REST Framework
    path('api/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/auth/', drf_views.obtain_auth_token, name='token'),
    # Fallout RPG
    path('', include(fallout_urls)),
    path('api/', include(fallout_api)),
]

# Common framework
if 'common' in settings.INSTALLED_APPS:
    from common.urls import urlpatterns as common_urls
    from common.api.urls import urlpatterns as common_api
    urlpatterns += [
        path('common/', include(common_urls, namespace='common')),
        path('api/common/', include(common_api, namespace='common-api'))]

# Debug
if settings.DEBUG:
    # Static and media files
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns += [path('debug/', include(debug_toolbar.urls))]
