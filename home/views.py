from django.views.generic.base import TemplateView

from products.models import Category, Product

class HomePage(TemplateView):
    template_name = 'home/home.html'

    def get_context_data(self, **kwargs):
        context = super(HomePage, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            parent=None, featured=True
        )
        context['products'] = Product.objects.filter(featured=True)
        return context
