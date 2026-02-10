import re
import csv
from django.core import management
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    '''Load a downloaded CSV of ManualParcelPINLink objects into the database and join to ZooniverseSubjects.'''

    def add_arguments(self, parser):

        parser.add_argument('-f', '--infile', type=str,
                            help='Path to CSV file of users, emails and passwords')
        
    def handle(self, *args, **kwargs):
        infile = kwargs['infile']
        
        if not infile:
            print('Missing infile path. Please specify with --infile.')
            return False
        else:

            print("Loading users...")

            group = Group.objects.get(name='Forsyth mappers')
            if group:

                with open(infile) as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        print(row['First Name'], row['Last Name'], row['Email'], row['Group ID'], row['username'], row['Password'])

                        # username = re.sub(r'[\'-]', "", f"{row['First Name'][0]}{row['Last Name']}").lower()
                        # print(username)

                        new_user = User(
                            first_name=row['First Name'],
                            last_name=row['Last Name'],
                            username=row['username'],
                            email=row['Email'],
                            password=make_password(row['Password']),
                            is_active=True,
                            is_staff=True
                        )

                        new_user.save()

                        new_user.groups.add(group)
                