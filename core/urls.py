from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from home.views import HomePage
from products.views import CategoryList

admin.site.site_title = 'SparedWares Admin'
admin.site.site_header = 'SparedWares Admin'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('categories', CategoryList.as_view(), name='categories'),

    path('', HomePage.as_view(), name='home'),
    path('', include('products.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
