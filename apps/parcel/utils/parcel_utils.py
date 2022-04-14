import re
import inflect

from apps.parcel.models import Parcel


def check_repeated_text_num(input_str):
    # Repeated text num, e.g. "six 6" or "6 six"
    r_text_num_left = re.search(r'(\d+) ([a-z\-]+)', input_str)
    if r_text_num_left:
        p = inflect.engine()
        test_left = p.number_to_words(r_text_num_left.group(1))
        test_right = r_text_num_left.group(2)
        if test_left and test_left == test_right:
            return r_text_num_left.group(1)

    # Same, but number on the right, parentheses optional
    r_text_num_right = re.search(r'([a-z\-]+) (?:\()?(\d+)(?:\))?', input_str)
    if r_text_num_right:
        p = inflect.engine()
        test_left = r_text_num_right.group(1)
        test_right = p.number_to_words(r_text_num_right.group(2))
        if test_right and test_left == test_right:
            return r_text_num_right.group(2)

    return None


def get_blocks(input_str):
    if input_str:
        # First, strip "block" and make all lowercase
        # input_str = input_str.lower().lstrip('block ')
        input_str = re.sub('Block ', '', input_str,
                           flags=re.IGNORECASE).lower()

        # Simple number
        simple_num = re.match(r'^\d+$', input_str)
        if simple_num:
            return input_str, 'simple_num'

        # Simple letter
        simple_letter = len(input_str) == 1 and re.match(r'[a-z]', input_str)
        if simple_letter:
            return input_str.upper(), 'simple_letter'

        repeated_text_num = check_repeated_text_num(input_str)
        if repeated_text_num:
            return repeated_text_num, 'repeated_text_num'

        # print(input_str)
    return None, None


def get_lots(input_str):
    if input_str:
        if re.match(r'none', input_str, flags=re.IGNORECASE):
            return None, None

        if re.search(r'partial', input_str, flags=re.IGNORECASE):
            return None, 'partial_lot'

        # First, strip "lot" and make all lowercase
        input_str = re.sub('lot(?:s)? ', '', input_str,
                           flags=re.IGNORECASE).lower()

        # Simple number
        simple_num = re.match(r'^\d+$', input_str)
        if simple_num:
            return [input_str], 'simple_num'

        repeated_text_num = check_repeated_text_num(input_str)
        if repeated_text_num:
            return [repeated_text_num], 'repeated_text_num'

        list_of_nums_preprocess = input_str.replace(', & ', ',').replace(' & ', ',').replace(', and', ',').replace(
            ' and ', ',').replace(', ', ',')
        list_of_nums = re.match(r'^[\d,]+$', list_of_nums_preprocess)
        if list_of_nums:
            return set(list_of_nums_preprocess.split(',')), 'list_of_nums'

    # print(f"{input_str}")
    return None, None


def standardize_addition(input_str):
    if input_str:
        input_str = re.sub(r'ADDIT\. ', 'ADDITION ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r'\'s', 's',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r's\'', 's',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r',(?: )?', ' ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r' & ', ' and ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r' (?:an )?addition to (?:the city of )?.+', ' ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r' addition', ' ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r'\s\s+', ' ', input_str)
        return input_str.lower().strip()
    return ''


def get_covenant_parcel_options(subject_obj):
    '''Get all possibilities for this ZooniverseSubject or ExtraParcelCandidate
    that can be attempted to be mapped,
    and characterize the number of lots found'''
    if hasattr(subject_obj, 'lot_final'):
        addition_attr = getattr(subject_obj, 'addition_final')
        block_attr = getattr(subject_obj, 'block_final')
        lot_attr = getattr(subject_obj, 'lot_final')
    else:
        addition_attr = getattr(subject_obj, 'addition')
        block_attr = getattr(subject_obj, 'block')
        lot_attr = getattr(subject_obj, 'lot')

    if hasattr(subject_obj, 'zooniverse_subject'):
        subject_id = subject_obj.zooniverse_subject.id
    else:
        subject_id = subject_obj.id

    out_candidates = []
    metadata = {}
    addition = standardize_addition(addition_attr)
    block, metadata['block'] = get_blocks(block_attr)
    lots, metadata['lot'] = get_lots(lot_attr)
    if block and lots:
        for lot in lots:
            out_candidates.append(
                {"subject_id": subject_id, "join_string": f"{addition} block {block} lot {lot}", "covenant_metadata": metadata})
    # print(blocks, block_style)
        return out_candidates, metadata
    return [], metadata


def get_all_parcel_options(parcel_obj):
    '''Get all possibilities for this Parcel that can be attempted to be mapped, and characterize the number of lots found and if they are the entire lot or a component'''

    out_candidates = []
    metadata = {'orig_filename': parcel_obj.orig_filename}
    addition = standardize_addition(parcel_obj.plat_name)

    block, metadata['block'] = get_blocks(parcel_obj.block)
    lots, metadata['lot'] = get_lots(parcel_obj.lot)
    if block and lots:
        for lot in lots:
            out_candidates.append(
                {"parcel_id": parcel_obj.id, "join_string": f"{addition} block {block} lot {lot}", "parcel_metadata": metadata})
    # print(blocks, block_style)
        return out_candidates, metadata
    return [], metadata


def build_parcel_spatial_lookups(workflow):
    print('Gathering all parcel records from this workflow...')
    parcel_spatial_lookup = {}

    # Basic lots
    for parcel in Parcel.objects.filter(
        workflow=workflow
    ).exclude(lot__isnull=True).only('id', 'plat_name', 'block', 'lot', 'orig_filename'):
        candidates, metadata = get_all_parcel_options(parcel)
        for c in candidates:
            parcel_spatial_lookup[c['join_string']] = c

    # TODO: How to dip into physical descriptions?

    # print(parcel_spatial_lookup)
    return parcel_spatial_lookup
