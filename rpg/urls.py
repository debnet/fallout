# coding: utf-8
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from rpg.fallout.urls import urlpatterns as fallout_urls, api_urlpatterns as fallout_api


admin.site.site_header = 'Fallout RPG'

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    # Fallout RPG
    url(r'^fallout/', include(fallout_urls)),
    url(r'^api/fallout/', include(fallout_api)),
]

# Common framework
if 'common' in settings.INSTALLED_APPS:
    from common.urls import urlpatterns as common_urls
    from common.api.urls import urlpatterns as common_api
    urlpatterns += [
        url(r'^common/', include(common_urls, namespace='common')),
        url(r'^api/common/', include(common_api, namespace='common-api')),
    ]

# Debug
if settings.DEBUG:
    # Static and media files
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns += [
            url(r'^debug/', include(debug_toolbar.urls)),
        ]
