from django.db import models

from mptt.models import MPTTModel, TreeForeignKey

from refinements.models import Aspect, Filter

class Category(MPTTModel):
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, related_name='children',
        blank=True, null=True
    )
    name = models.CharField(max_length=150, db_index=True)
    slug = models.SlugField(max_length=150, unique=True)
    nickname = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    ebay_cat = models.CharField(max_length=25)
    featured = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'categories'

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.nickname if self.nickname else self.name

class Product(MPTTModel):
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, related_name='children',
        blank=True, null=True
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=150, db_index=True)
    slug = models.SlugField(max_length=150, unique=True)
    nickname = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    query = models.CharField(max_length=100, blank=True)
    aspects = models.ManyToManyField(Aspect, blank=True)
    filters = models.ManyToManyField(Filter, blank=True)
    featured = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class MPTTMeta:
        order_insertion_by = ['category', '-order', 'name']

    def __str__(self):
        return self.nickname if self.nickname else self.name
