import json

from django.views.generic import list, detail
from django.http import JsonResponse
from django.template import loader

from refinements.models import Filter
from ebay.items import ItemResponse

from .models import Category, Product

class CategoryList(list.ListView):
    model = Category
    template_name = 'products/categories.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return super(CategoryList, self).get_queryset().filter(parent=None)

class CategoryPage(detail.DetailView):
    model = Category
    template_name = 'products/category.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super(CategoryPage, self).get_context_data(**kwargs)
        context['children'] = self.object.get_descendants()
        context['products'] = Product.objects.filter(
            category__slug=self.kwargs['slug']
        )
        return context

class ProductPage(detail.DetailView):
    model = Product
    template_name = 'products/product.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super(ProductPage, self).get_context_data(**kwargs)
        context['models'] = self.object.get_children()
        context['filters'] = Filter.objects.filter(
            product__in=self.object.get_family()
        ).distinct()
        context['items'] = ItemResponse(self.request, self.object).get_items()
        context['query'] = json.dumps(dict(self.request.GET))
        return context

def ajax(request, category, slug):
    """
    Pull new page of Ebay items on load button press

    Parameters:
        request (HttpRequest): Current HTTP Request object
        category: Product category
        slug (string): Product url string

    Returns:
        JsonResponse: Next page of Ebay listings
    """
    items = ItemResponse(request, Product.objects.get(
        category__slug=category, slug=slug
    )).get_items()
    items_html = loader.render_to_string(
        'products/results.html', {'items': items}
    )
    return JsonResponse({'items_html': items_html})
