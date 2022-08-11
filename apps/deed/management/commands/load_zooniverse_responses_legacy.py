import os
import datetime

from apps.deed.models import ZooniverseResponseRaw, Workflow, PotentialMatch, ZooniverseUser, ZooniverseResponseFlat
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    '''DEPRECATED: Bulk load raw Zooniverse export data for further processing'''
    question_lookup = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def load_csv(self):
        '''
        Implements a django-postgres-copy loader to bulk load raw Zooniverse responses into the ZooniverseResponseRaw model.

        TK: Move CSV path to question lookup in local settings
        '''
        print("Loading raw Zooniverse export data...")
        import_csv = os.path.join(settings.BASE_DIR, 'data', 'zooniverse_exports',
                                  'mapping-prejudice-classifications_2_23_2021.csv')

        # Make custom mapping from model fields to drop IP column
        mapping = {f.name: f.name for f in ZooniverseResponseRaw._meta.get_fields(
        ) if f.name not in ['id', 'subject_data_flat', 'zooniverseresponseflat']}

        insert_count = ZooniverseResponseRaw.objects.from_csv(
            import_csv, mapping=mapping)
        print("{} records inserted".format(insert_count))

    def create_new_subjects(self, workflow, responses) -> dict:
        '''Creates any non-existant subject records in bulk, and returns a lookup table of zooniverse subject ids to django db pks for us in fast creation of flat classification records'''
        print('Creating missing matches ...')

        existing_match_ids = PotentialMatch.objects.filter(
            workflow=workflow).values_list('zoon_subject_id', flat=True)

        import_match_ids = responses.values_list('subject_ids', flat=True)
        match_ids_to_create = list(
            set(import_match_ids) - set(existing_match_ids))

        new_matches = []
        for m in match_ids_to_create:
            p_match = PotentialMatch(
                workflow=workflow,
                zoon_subject_id=m
            )
            new_matches.append(p_match)
        PotentialMatch.objects.bulk_create(new_matches, 10000)

        batch_matches = PotentialMatch.objects.filter(
            workflow=workflow, zoon_subject_id__in=import_match_ids).values('id', 'zoon_subject_id')

        return {b['zoon_subject_id']: b['id'] for b in batch_matches}

    def create_new_users(self, responses) -> dict:
        '''Creates any non-existant user records in bulk, and returns a lookup table of zooniverse usr names to django db pks for us in fast creation of flat classification records. Using names because some zooniverse users are not logged in so their user id is null'''
        print('Creating missing users ...')

        # existing_user_ids = ZooniverseUser.objects.all().values_list('zoon_id', flat=True)
        existing_user_names = ZooniverseUser.objects.all().values_list('zoon_name', flat=True)

        import_users = responses.values('user_id', 'user_name').distinct()
        # import_user_ids = [u['user_id'] for u in import_users]
        import_user_names = [u['user_name'] for u in import_users]

        # user_ids_to_create = list(set(import_user_ids) - set(existing_user_ids))
        user_names_to_create = list(
            set(import_user_names) - set(existing_user_names))

        new_users = []
        for nu in user_names_to_create:
            if nu:
                user = ZooniverseUser(
                    # zoon_id=nu,
                    # zoon_name=[u['user_name'] for u in import_users if u['user_id'] == nu][0]
                    zoon_id=[u['user_id']
                             for u in import_users if u['user_name'] == nu][0],
                    zoon_name=nu
                )
                new_users.append(user)
        ZooniverseUser.objects.bulk_create(new_users, 10000)

        batch_users = ZooniverseUser.objects.filter(
            zoon_name__in=import_user_names).values('id', 'zoon_name')

        return {b['zoon_name']: b['id'] for b in batch_users}

    def answer_finder(self, annotations, field):
        '''Returns boolean or string depending on answer type'''
        if self.question_lookup[field] is not None:
            try:
                answer = [a['value'] for a in annotations if a['task']
                          == self.question_lookup[field]][0]
                if answer == 'Yes':
                    return True
                if answer == 'No':
                    return False
                return answer
            except:
                print(annotations)
                return ''
        return ''

    def zooniverse_combo_attr(self, combo_response, q_name):
        return [a for a in combo_response if a['task'] == q_name][0]['value'][0]['label']

    def zooniverse_date_parser(self, annotations, date_lookup):
        '''Pastes together a date from Zooniverse response, assuming a "3-task combo" in the Zooniverse workflow with separate pulldowns for year, month, day'''
        try:
            date_answers = [a['value']
                            for a in annotations if a['task'] == date_lookup['root_q']][0]
        except:
            print("Couldn't find date object in expected format.")
            return None

        year = self.zooniverse_combo_attr(date_answers, date_lookup['year'])
        month = self.zooniverse_combo_attr(date_answers, date_lookup['month'])
        day = self.zooniverse_combo_attr(date_answers, date_lookup['day'])

        month_value = int(month.split(' - ')[0])
        try:
            return datetime.datetime(int(year), month_value, int(day)).date()
        except ValueError as error:
            print('Could not parse final date.')
            return None

    def normalize_responses(self, workflow_name: str):
        print('Created normalized records for retired subject responses...')
        # Only get retired subjects
        responses = ZooniverseResponseRaw.objects.filter(
            workflow_name=workflow_name).exclude(subject_data_flat__retired=None)

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

        print('Parsing classification records ...')

        flat_responses = []
        for r in responses:
            bool_covenant_text = self.answer_finder(
                r.annotations, 'bool_covenant')

            if bool_covenant_text == "I can't figure this one out":
                bool_covenant = None
                bool_outlier = True
                covenant_text = addition = lot = block = seller = buyer = ''
                deed_date = None
                dt_retired = r.subject_data_flat['retired']['retired_at']
            elif bool_covenant_text is True:
                bool_covenant = True
                bool_outlier = False
                covenant_text = self.answer_finder(
                    r.annotations, 'covenant_text')
                addition = self.answer_finder(r.annotations, 'addition')
                lot = self.answer_finder(r.annotations, 'lot')
                block = self.answer_finder(r.annotations, 'block')
                seller = self.answer_finder(r.annotations, 'seller')
                buyer = self.answer_finder(r.annotations, 'buyer')
                deed_date = self.zooniverse_date_parser(
                    r.annotations, self.question_lookup['deed_date'])
                dt_retired = r.subject_data_flat['retired']['retired_at']
            elif bool_covenant_text is False:
                bool_covenant = False
                bool_outlier = False
                dt_retired = r.subject_data_flat['retired']['retired_at']
                covenant_text = addition = lot = block = seller = buyer = ''
                deed_date = None

            # TODO: Handle "partial"

            response = ZooniverseResponseFlat(
                workflow_id=workflow.id,
                subject_id=match_lookup[r.subject_ids],
                # user_id=user_lookup[r.user_id] if r.user_id else None,
                user_id=user_lookup[r.user_name],
                classification_id=r.classification_id,

                bool_covenant=bool_covenant,
                bool_outlier=bool_outlier,
                covenant_text=covenant_text,
                addition=addition,
                lot=lot,
                block=block,
                seller=seller,
                buyer=buyer,
                deed_date=deed_date,

                dt_created=r.created_at,
                dt_retired=dt_retired,

                raw_match_id=r.id
            )

            flat_responses.append(response)

        print('Saving normalized objects to DB...')
        ZooniverseResponseFlat.objects.bulk_create(flat_responses, 10000)

    def flatten_subject_data(self, workflow_name: str):
        '''
        The raw "subject_data" coming back from Zooniverse is a JSON object with the key of the "subject_id". The data being stored behind this key cannot easily be queried by Django, but if we flatten it, we can. This creates a flattened copy of the subject_data field to make querying easier, and updates the raw responses in bulk.
        '''
        print("Creating flattened version of subject_data...")
        responses = ZooniverseResponseRaw.objects.filter(
            workflow_name=workflow_name).only('subject_data')

        for response in responses:
            first_key = next(iter(response.subject_data))
            response.subject_data_flat = response.subject_data[first_key]

        ZooniverseResponseRaw.objects.bulk_update(
            responses, ['subject_data_flat'], 10000)  # Batches of 10,000 records at a time

    def check_import(self, workflow_name: str):
        '''Make sure no raw subjects in this batch didn't make it to the ZooniverseResponseFlat model, excluding un-retired subjects'''
        print('Checking for missing subjects ...')
        missing_subjects = ZooniverseResponseRaw.objects.filter(
            workflow_name=workflow_name,
            zooniverseresponseflat__isnull=True
        ).exclude(subject_data_flat__retired=None)

        print(f'Found {missing_subjects.count()} missing subjects.')

        for zr in missing_subjects:
            print(zr.id)
            print(zr.annotations)

    def clear_all_tables(self, workflow_name: str):
        print('WARNING: Clearing all tables before import...')
        ZooniverseResponseRaw.objects.filter(
            workflow_name=workflow_name).delete()
        Workflow.objects.filter(workflow_name=workflow_name).delete()
        PotentialMatch.objects.filter(
            workflow__workflow_name=workflow_name).delete()
        # ZooniverseUser.objects.all().delete()
        ZooniverseResponseFlat.objects.filter(
            workflow__workflow_name=workflow_name).delete()

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            self.question_lookup = settings.ZOONIVERSE_QUESTION_LOOKUP[
                workflow_name]['zozooniverse_config']

            self.clear_all_tables(workflow_name)
            self.load_csv()
            self.flatten_subject_data(workflow_name)
            self.normalize_responses(workflow_name)
            self.check_import(workflow_name)
