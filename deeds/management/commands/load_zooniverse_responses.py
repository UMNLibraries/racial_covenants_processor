import os

from deeds.models import ZooniverseResponseRaw, Workflow, PotentialMatch, ZooniverseUser, ZooniverseResponseFlat
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    '''Bulk load raw Zooniverse export data for further processing'''

    question_lookup = {
        'bool_covenant': 'T0',
        'covenant_text': 'T2',
        'addition': 'T9',
        'lot': 'T5',
        'block': 'T7',
        'seller': None,
        'buyer': None,
        'deed_date_year': 'T15',
        'deed_date_month': 'T16',
        'deed_date_day': 'T17',
    }

    def load_csv(self):
        '''
        Implements a django-postgres-copy loader to bulk load raw Zooniverse responses into the ZooniverseResponseRaw model.
        '''
        print("Loading raw Zooniverse export data...")
        import_csv = os.path.join(settings.BASE_DIR, 'data', 'zooniverse_exports', 'mapping-prejudice-classifications_2_23_2021.csv')

        # Make custom mapping from model fields to drop IP column
        mapping = {f.name: f.name for f in ZooniverseResponseRaw._meta.get_fields() if f.name != 'id'}

        insert_count = ZooniverseResponseRaw.objects.from_csv(import_csv, mapping=mapping)
        print("{} records inserted".format(insert_count))

    def create_new_subjects(self, workflow, responses) -> dict:
        '''Creates any non-existant subject records in bulk, and returns a lookup table of zooniverse subject ids to django db pks for us in fast creation of flat classification records'''
        existing_match_ids = PotentialMatch.objects.filter(workflow=workflow).values_list('zoon_subject_id', flat=True)

        import_match_ids = responses.values_list('subject_ids', flat=True)
        match_ids_to_create = list(set(import_match_ids) - set(existing_match_ids))

        new_matches = []
        for m in match_ids_to_create:
            p_match = PotentialMatch(
                workflow=workflow,
                zoon_subject_id=m
            )
            new_matches.append(p_match)
        PotentialMatch.objects.bulk_create(new_matches, 10000)

        batch_matches = PotentialMatch.objects.filter(workflow=workflow, zoon_subject_id__in=import_match_ids).values('id', 'zoon_subject_id')

        return {b['zoon_subject_id']: b['id'] for b in batch_matches}

    def create_new_users(self, responses) -> dict:
        '''Creates any non-existant user records in bulk, and returns a lookup table of zooniverse usr ids to django db pks for us in fast creation of flat classification records'''

        existing_user_ids = ZooniverseUser.objects.all().values_list('zoon_id', flat=True)

        import_users = responses.values('user_id', 'user_name').distinct()
        import_user_ids = [u['user_id'] for u in import_users]

        user_ids_to_create = list(set(import_user_ids) - set(existing_user_ids))

        new_users = []
        for u in user_ids_to_create:
            user = ZooniverseUser(
                zoon_id=u,
                zoon_name=[u['user_name'] for u in import_users][0]
            )
            new_users.append(user)
        ZooniverseUser.objects.bulk_create(new_users, 10000)

        batch_users = ZooniverseUser.objects.filter(zoon_id__in=import_user_ids).values('id', 'zoon_id')

        return {b['zoon_id']: b['id'] for b in batch_users}

    def answer_finder(self, annotations, field):
        if self.question_lookup[field] is not None:
            try:
                answer = [a['value'] for a in annotations if a['task'] == self.question_lookup[field]][0]
                if answer == 'Yes':
                    return True
                if answer == 'No':
                    return False
                return answer
            except:
                print(annotations)
                return None
        return None

    def normalize_responses(self, workflow_name:str):
        responses = ZooniverseResponseRaw.objects.filter(workflow_name=workflow_name)

        try:
            workflow, w_created = Workflow.objects.get_or_create(
                zoon_id=responses[0].workflow_id,
                workflow_name=workflow_name
            )
            if w_created:
                print(f"New workflow record created for {workflow_name}.")
        except:
            print("No matching workflow found in Zooniverse responses.")
            raise

        # Create any missing match instances
        match_lookup = self.create_new_subjects(workflow, responses)

        # Create any missing user instances
        user_lookup = self.create_new_users(responses)

        flat_responses = []
        for r in responses[0:1000]:
            bool_covenant_text = self.answer_finder(r.annotations, 'bool_covenant')

            if bool_covenant_text == "I can't figure this one out":
                bool_covenant = None
                bool_outlier = True
                covenant_text = addition = lot = block = seller = buyer = ''
            elif bool_covenant_text is True:
                bool_covenant = True
                bool_outlier = False
                covenant_text = self.answer_finder(r.annotations, 'covenant_text')
                addition = self.answer_finder(r.annotations, 'addition')
                print(addition)
                lot = self.answer_finder(r.annotations, 'lot')
                block = self.answer_finder(r.annotations, 'block')
                seller = self.answer_finder(r.annotations, 'seller')
                buyer = self.answer_finder(r.annotations, 'buyer')
            elif bool_covenant_text is False:
                bool_covenant = False
                bool_outlier = False
                covenant_text = addition = lot = block = seller = buyer = ''

            response = ZooniverseResponseFlat(
                workflow_id=workflow.id,
                subject_id=match_lookup[r.subject_ids],
                user_id=user_lookup[r.user_id] if r.user_id else None,
                classification_id=r.classification_id,

                bool_covenant=bool_covenant,
                bool_outlier=bool_outlier,
                covenant_text=covenant_text,
                addition=addition,
                lot=lot,
                block=block,
                seller=seller,
                buyer=buyer,
                # TODO: deed_date=self.answer_finder(r.annotations, 'deed_date'),

                dt_created=r.created_at
                # TODO: dt_retired=?
            )

            flat_responses.append(response)

        ZooniverseResponseFlat.objects.bulk_create(flat_responses, 10000)

    def flatten_subject_data(self):
        '''
        The raw "subject_data" coming back from Zooniverse is a JSON object with the key of the "subject_id". The data being stored behind this key cannot easily be queried by Django, but if we flatten it, we can. This creates a flattened copy of the subject_data field to make querying easier, and updates the raw responses in bulk.
        '''
        print("Creating flattened version of subject_data...")
        responses = ZooniverseResponseRaw.objects.all().only('subject_data')

        for response in responses:
            first_key = next(iter(response.subject_data))
            response.subject_data_flat = response.subject_data[first_key]

        ZooniverseResponseRaw.objects.bulk_update(responses, ['subject_data_flat'], 10000)  # Batches of 10,000 records at a time

    def handle(self, *args, **kwargs):
        # self.load_csv()
        # Get rid of subject_id lookup on subject_data to make querying in Django easier
        # self.flatten_subject_data()
        ZooniverseResponseFlat.objects.all().delete()
        self.normalize_responses('Ramsey County')
