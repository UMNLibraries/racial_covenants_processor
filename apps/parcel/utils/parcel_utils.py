import re
import inflect


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

        if str(input_str).lower() == 'none':
            return 'none', 'no_block'

        return input_str, None
    return 'none', 'no_block'


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
            return sorted(set(list_of_nums_preprocess.split(','))), 'list_of_nums'

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


def write_join_strings(addition_raw, block_raw, lot_raw):
    '''More low-level, to generate the actual string, using string values'''
    out_candidates = []
    metadata = {}
    addition = standardize_addition(addition_raw)
    block, metadata['block'] = get_blocks(block_raw)
    lots, metadata['lot'] = get_lots(lot_raw)
    if lots:  # Allow blank lot
        for lot in lots:
            out_candidates.append(
                {"join_string": f"{addition} block {block} lot {lot}", "metadata": metadata})
    # print(blocks, block_style)
        return out_candidates
    return []


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

    join_strings = write_join_strings(addition_attr, block_attr, lot_attr)

    for candidate in join_strings:
        candidate['subject_id'] = subject_id
    return join_strings


def get_all_parcel_options(parcel_obj):
    '''Get all possibilities for this Parcel that can be attempted to be mapped, and characterize the number of lots found and if they are the entire lot or a component'''

    out_candidates = []
    metadata = {'orig_filename': parcel_obj.orig_filename}
    # addition = standardize_addition(parcel_obj.plat_name)
    addition = parcel_obj.plat_standardized

    # Check for alternate addition spellings
    extra_additions = []
    if parcel_obj.plat:
        if parcel_obj.plat.platalternatename_set.count() > 0:
            for p in parcel_obj.plat.platalternatename_set.all():
                extra_additions.append(p.alternate_name_standardized)

    join_strings = []
    for a in [addition] + extra_additions:
        join_strings += write_join_strings(a, parcel_obj.block, parcel_obj.lot)

    for candidate in join_strings:
        candidate['parcel_id'] = parcel_obj.id
    return join_strings


def build_parcel_spatial_lookups(workflow):
    from apps.parcel.models import ParcelJoinCandidate
    print('Gathering all parcel records from this workflow...')
    parcel_spatial_lookup = {}

    # Basic lots
    for candidate in ParcelJoinCandidate.objects.filter(
        workflow=workflow
    ).exclude(join_string='').values('parcel__id', 'join_string', 'metadata'):
        parcel_spatial_lookup[candidate['join_string']] = {
            'parcel_id': candidate['parcel__id'],
            'parcel_metadata': candidate['metadata']
        }

    # TODO: How to dip into physical descriptions?
    return parcel_spatial_lookup


def gather_all_covenant_candidates(subject_obj):
    candidates = get_covenant_parcel_options(subject_obj)
    if subject_obj.extraparcelcandidate_set.count() > 0:
        for extra_parcel in subject_obj.extraparcelcandidate_set.all():
            candidates += get_covenant_parcel_options(extra_parcel)

    return list({v['join_string']:v for v in candidates}.values())
