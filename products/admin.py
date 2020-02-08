from django.contrib import admin
from django import forms

from mptt.admin import MPTTModelAdmin
from mptt.forms import TreeNodeChoiceField

from .models import Category, Product

class CategoryAdmin(MPTTModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class ProductAdmin(MPTTModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['aspects', 'filters']

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
