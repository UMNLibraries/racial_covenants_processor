from django.db import models
from django.utils.text import slugify

from apps.zoon.models import ZooniverseWorkflow
from racial_covenants_processor.storage_backends import PrivateMediaStorage


class Plat(models.Model):
    workflow = models.ForeignKey(ZooniverseWorkflow, on_delete=models.SET_NULL)
    plat_name = models.CharField(max_length=255, db_index=True, null=True)
    book_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True)
    gov_id = models.CharField(
        max_length=255, db_index=True, null=True, blank=True)

    def slug(self):
        return slugify(f"{self.workflow.slug} {self.name}")

    def __str__(self):
        return self.plat_name


class PlatMapPage(models.Model):
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE)
    page_num = models.IntegerField(null=True)
    page_image_web = models.ImageField(
        storage=PrivateMediaStorage(), null=True)


class PlatAlternateName(models.Model):
    workflow = models.ForeignKey(ZooniverseWorkflow, on_delete=models.SET_NULL)
    plat = models.ForeignKey(Plat, on_delete=models.SET_NULL)
    plat_name = models.CharField(max_length=255, db_index=True, null=True)
    alternate_name = models.CharField(max_length=255, db_index=True, null=True)
