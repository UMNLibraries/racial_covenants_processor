from django.core.files.storage import storages
from storages.backends.s3boto3 import S3Boto3Storage
# https://testdriven.io/blog/storing-django-static-and-media-files-on-amazon-s3/


class StaticStorage(S3Boto3Storage):
    '''Not actually being used?'''
    location = 'static'
    default_acl = 'public-read'


class PublicMediaStorage(S3Boto3Storage):
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    location = ''
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False


class PublicDeedStorage(S3Boto3Storage):
    '''for anonymized web images of deeds only'''
    location = ''
    default_acl = 'public-read'
    file_overwrite = False
    custom_domain = False


class CachedS3BotoStorage(S3Boto3Storage):
    """
    S3 storage backend that saves the files locally, too.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_storage = storages.create_storage({
            "BACKEND": "compressor.storage.CompressorFileStorage"
        })
        self.default_acl = 'public-read'

    def save(self, name, content):
        self.local_storage.save(name, content)
        super().save(name, self.local_storage._open(name))
        return name