import re
import boto3

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.conf import settings


class Command(BaseCommand):

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    s3 = None
    bucket = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def delete_in_batches(self, objects_to_delete, batch_size=1000):
        print(f'Deleting {len(objects_to_delete)} s3 files ...')

        for i in range(0, len(objects_to_delete), batch_size):
            response = self.bucket.delete_objects(Delete={
                    'Objects': objects_to_delete[i:i+batch_size]
                })

            # print(response)

    def delete_raw(self, workflow_slug):

        key_filter = re.compile(fr"raw/{workflow_slug}/.+\.(?:tif|TIF|tiff|jpg|JPG|JPEG)")

        objects_to_delete = [{'Key': obj.key} for obj in self.bucket.objects.filter(
                Prefix=f'raw/{workflow_slug}/'
            ) if re.match(key_filter, obj.key)]

        self.delete_in_batches(objects_to_delete)

    # def delete_web(self, workflow_slug):

    #     key_filter = re.compile(fr"web/{workflow_slug}/.+\.jpg")

    #     objects_to_delete = [{'Key': obj.key} for obj in self.bucket.objects.all(
    #     ) if re.match(key_filter, obj.key)]

    #     self.delete_in_batches(objects_to_delete)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            workflow_slug = slugify(workflow_name)

            confirm = input(
                'You are about to delete a lot of images from s3. Are you sure? (Y/n)')
            while 1:
                if confirm not in ('Y', 'n', 'yes', 'no'):
                    confirm = input('Please enter either "yes" or "no": ')
                    continue
                if confirm in ('Y', 'yes'):
                    break
                else:
                    return

            self.s3 = self.session.resource('s3')
            self.bucket = self.s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

            self.delete_raw(workflow_slug)
            # self.delete_web(workflow_slug)
