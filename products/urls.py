from django.urls import path

from .views import CategoryPage, ProductPage, ajax

urlpatterns = [
    path('ajax/<slug:category>/<slug:slug>', ajax, name='ajax'),
    path('<slug:slug>', CategoryPage.as_view(), name='category'),
    path(
        '<slug:category>/<slug:slug>',
        ProductPage.as_view(), name='product'
    ),
]
