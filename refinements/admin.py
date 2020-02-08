from django.contrib import admin

from .models import Aspect, Group, Filter

class AspectAdmin(admin.ModelAdmin):
    search_fields = ['name', 'value']

class GroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class FilterAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('value',)}
    search_fields = ['group__name', 'value']
    autocomplete_fields = ['aspects']

admin.site.register(Aspect, AspectAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Filter, FilterAdmin)
