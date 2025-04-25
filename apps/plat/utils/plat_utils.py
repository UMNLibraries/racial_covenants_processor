from apps.plat.models import Subdivision

from apps.parcel.utils.parcel_utils import standardize_addition

def standardize_subdivisions(workflow):
    ''' Standardize each unique addition name, and save back to Subdivision objects with that plat_name'''
    print('Standardizing subdivision names...')

    subdivisions = Subdivision.objects.filter(
        workflow=workflow)
    subs_to_update = []
    for s in Subdivision.objects.filter(workflow=workflow).only('name', 'name_standardized'):
        s.name_standardized = standardize_addition(s.name)
        print(f'{s.name} --> {s.name_standardized}')
        subs_to_update.append(s)

    print(f'Updating {len(subs_to_update)} subdivisions ...')
    Subdivision.objects.bulk_update(
        subs_to_update, ['name_standardized'])