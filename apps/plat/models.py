from django.db import models
from django.utils.text import slugify
from django.utils.html import mark_safe

from apps.zoon.models import ZooniverseWorkflow
from racial_covenants_processor.storage_backends import PrivateMediaStorage


class Plat(models.Model):
    workflow = models.ForeignKey(
        ZooniverseWorkflow, null=True, on_delete=models.SET_NULL)
    plat_name = models.CharField(max_length=255, db_index=True, null=True)
    plat_year = models.IntegerField(null=True, blank=True)
    book_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True)
    gov_id = models.CharField(
        max_length=255, null=True, blank=True)  # Can't be an index because some plat maps have multiple plats on same map page. Maybe revisit this later

    class Meta:
        ordering = ["plat_name"]

    def slug(self):
        return slugify(f"{self.workflow.slug} {self.name}")

    def __str__(self):
        return self.plat_name


class PlatMapPage(models.Model):
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE)
    page_num = models.IntegerField(null=True)
    remote_link = models.URLField(blank=True)
    page_image_web = models.ImageField(
        storage=PrivateMediaStorage(), null=True)

    @property
    def thumbnail_preview(self):
        print(self.page_image_web)
        if self.page_image_web:
            return mark_safe(f'<a href="{self.page_image_web.url}" target="_blank"><img src="{self.page_image_web.url}" width="100" /></a>')
        return ""


class PlatAlternateName(models.Model):
    workflow = models.ForeignKey(
        ZooniverseWorkflow, null=True, on_delete=models.SET_NULL)
    plat = models.ForeignKey(Plat, null=True, on_delete=models.SET_NULL)
    plat_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True)
    alternate_name = models.CharField(max_length=255, db_index=True, null=True)

    def save(self, *args, **kwargs):
        self.plat_name = self.plat.plat_name
        super(PlatAlternateName, self).save(*args, **kwargs)
