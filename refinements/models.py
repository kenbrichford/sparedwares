from django.db import models

class Aspect(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    value = models.CharField(max_length=50, db_index=True)
    is_strict = models.BooleanField(default=False)

    class Meta:
        ordering = ['name', 'value']

    def __str__(self):
        return '%s: %s' % (self.name, self.value)

class Group(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    slug = models.SlugField(max_length=50, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class Filter(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    value = models.CharField(max_length=50, db_index=True)
    slug = models.SlugField(max_length=50)
    aspects = models.ManyToManyField(Aspect, blank=True)
    query = models.CharField(max_length=50, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['group', '-order', 'value']
        unique_together = ('group', 'slug')

    def __str__(self):
        return '%s: %s' % (self.group.name, self.value)
