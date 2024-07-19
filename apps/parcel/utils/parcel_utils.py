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


def strip_leading_0s_str(input_str):
    return str(input_str).lstrip('0')


def strip_leading_0s_list(input_list):
    return [str(x).lstrip('0') for x in input_list]


def get_blocks(input_str):
    if input_str:
        # First, strip "block" and make all lowercase
        # input_str = input_str.lower().lstrip('block ')
        input_str = re.sub('Block ', '', input_str,
                           flags=re.IGNORECASE).lower()

        # Simple number
        simple_num = re.match(r'^\d+$', input_str)
        if simple_num:
            return strip_leading_0s_str(input_str), 'simple_num'

        # Simple letter
        simple_letter = len(input_str) == 1 and re.match(r'[a-z]', input_str)
        if simple_letter:
            return strip_leading_0s_str(input_str.upper()), 'simple_letter'

        repeated_text_num = check_repeated_text_num(input_str)
        if repeated_text_num:
            return strip_leading_0s_str(repeated_text_num), 'repeated_text_num'

        if str(input_str).lower() == 'none':
            return 'none', 'no_block'

        return input_str, None
    return 'none', 'no_block'


def get_lots(input_str):
    if input_str:
        input_str = input_str.strip()

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
            return strip_leading_0s_list([input_str]), 'simple_num'

        repeated_text_num = check_repeated_text_num(input_str)
        if repeated_text_num:
            return strip_leading_0s_list([repeated_text_num]), 'repeated_text_num'

        num_range = re.search(r'^(\d+)(?:-| thru )(\d+)$', input_str)
        if num_range:
            start = int(num_range.group(1))
            end = int(num_range.group(2))
            return strip_leading_0s_list(list(range(start, end+1))), 'num_range'

        simple_multi_lot = [x.group() for x in re.finditer(r'(?:((?:(?<=^)|(?<=^LOTS )|(?<=& ))\d+(?= |$)))', input_str)]
        if len(simple_multi_lot) > 0:
            return strip_leading_0s_list(simple_multi_lot), 'simple_multi_lot'

        list_of_nums_preprocess = input_str.replace(', & ', ',').replace(' & ', ',').replace(', and', ',').replace(
            ' and ', ',').replace(', ', ',')
        list_of_nums = re.match(r'^[\d,]+$', list_of_nums_preprocess)
        if list_of_nums:
            return strip_leading_0s_list(sorted(set(list_of_nums_preprocess.split(',')))), 'list_of_nums'

    return None, None


def standardize_addition(input_str):
    if input_str:
        # replace ordinal words with numerical abbreviations
        for word, abbr in {
            'first': '1st',
            'second': '2nd',
            'third': '3rd',
            'fourth': '4th',
            'fifth': '5th',
            'sixth': '6th',
            'seventh': '7th',
            'eighth': '8th',
            'ninth': '9th',
            'tenth': '10th',
        }.items():
            input_str = re.sub(f'{word}', f'{abbr}',
                           input_str, flags=re.IGNORECASE)

        # apostrophe with 's or 'n (ass'n)
        input_str = re.sub(r'[\'`’]([sn])', r'\1',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r'([sn])[\'`’]', r'\1',
                           input_str, flags=re.IGNORECASE)
        # Variations of "addition"
        input_str = re.sub(r'ADD(?:IT)?\.', 'ADDITION',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r' ADDN(\.)?', ' ADDITION',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r' ADD(\.)?$', ' ADDITION',
                           input_str, flags=re.IGNORECASE)
        # Sometimes it's misspelled
        input_str = re.sub(r'SUBDIVSION', 'SUBDIVISION',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r'RE-SUB', 'RESUB',
                           input_str, flags=re.IGNORECASE)
        # SUBD abbreviation followed by space or end of string
        input_str = re.sub(r'SUBD*\.*(?=\s|$)', 'SUBDIVISION',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r',(?: )?', ' ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r' & ', ' and ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r' no(\.)?\s*(?=\d+)', ' ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r'#\s*(?=\d+)', '',
                           input_str, flags=re.IGNORECASE)
        # Some weird cases (Crow Wing County) where it's not an addition to a city, so leave those alone (the (?<=.{4}) part)
        input_str = re.sub(r'(?<=.{5}) (?:an )?addition to (?:the city of )?.+', ' ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r'\.\s*', ' ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r' addition', ' ',
                           input_str, flags=re.IGNORECASE)
        input_str = re.sub(r' subdivision', ' ',
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
    '''Get all possibilities for this ZooniverseSubject, ExtraParcelCandidate or ManualParcel
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
        if addition != parcel_obj.plat.plat_name_standardized:
            extra_additions.append(parcel_obj.plat.plat_name_standardized)
        if parcel_obj.plat.platalternatename_set.count() > 0:
            for p in parcel_obj.plat.platalternatename_set.all():
                extra_additions.append(p.alternate_name_standardized)

    if parcel_obj.subdivision_spatial:
        if addition != parcel_obj.subdivision_spatial.name_standardized:
            extra_additions.append(parcel_obj.subdivision_spatial.name_standardized)
        if parcel_obj.subdivision_spatial.subdivisionalternatename_set.count() > 0:
            for p in parcel_obj.subdivision_spatial.subdivisionalternatename_set.all():
                extra_additions.append(p.alternate_name_standardized)

    join_strings = []
    for a in [addition] + extra_additions:
        join_strings += write_join_strings(a, parcel_obj.block, parcel_obj.lot)

    # ManualParcelCandidates
    for mpc in parcel_obj.manualparcelcandidate_set.all():
        join_strings += write_join_strings(mpc.addition, mpc.block, mpc.lot)

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
        # Allow for multiple parcels with same lot combo, does happen with adjacent lots
        if candidate['join_string'] not in parcel_spatial_lookup:
            parcel_spatial_lookup[candidate['join_string']] = {
                'parcel_ids': [candidate['parcel__id']],
                'parcel_metadata': candidate['metadata']
            }
        else:
            parcel_spatial_lookup[candidate['join_string']]['parcel_ids'].append(candidate['parcel__id'])

    # TODO: How to dip into physical descriptions?
    return parcel_spatial_lookup


def gather_all_covenant_candidates(subject_obj):
    candidates = get_covenant_parcel_options(subject_obj)
    if subject_obj.extraparcelcandidate_set.count() > 0:
        for extra_parcel in subject_obj.extraparcelcandidate_set.all():
            candidates += get_covenant_parcel_options(extra_parcel)

    return list({v['join_string']: v for v in candidates}.values())


def gather_all_manual_covenant_candidates(manualcovenant_obj):
    # Might need to add alternative extra parcel candidate model here in the future
    candidates = get_covenant_parcel_options(manualcovenant_obj)
    return list({v['join_string']: v for v in candidates}.values())


def addition_wide_parcel_match(cov_obj):
    '''Generally runs inside save routines of ZooniverseSubject and ManualCovenant'''
    from apps.plat.models import Plat, PlatAlternateName, Subdivision, SubdivisionAlternateName
    from apps.parcel.models import Parcel

    if hasattr(cov_obj, 'addition_final'):
        plat_name_standardized = standardize_addition(cov_obj.addition_final)
    else:
        plat_name_standardized = standardize_addition(cov_obj.addition)

    # Lookup by addition name
    if plat_name_standardized not in [None, '']:
        matching_parcels = Parcel.objects.filter(workflow=cov_obj.workflow, plat_standardized=plat_name_standardized)
        if matching_parcels.count() > 0:
            cov_obj.bool_parcel_match = True
            cov_obj.parcel_matches.add(*matching_parcels.all())

    # Lookup by plat map obj
    matching_plats = Plat.objects.filter(workflow=cov_obj.workflow, plat_name_standardized=plat_name_standardized)
    matching_plat_alternates = PlatAlternateName.objects.filter(workflow=cov_obj.workflow, alternate_name_standardized=plat_name_standardized)

    if matching_plats.count() > 0:
        cov_obj.bool_parcel_match = True
        for p in matching_plats:
            cov_obj.parcel_matches.add(*p.parcel_set.all())

    # Lookup by alternate name
    elif matching_plat_alternates.count() > 0:
        cov_obj.bool_parcel_match = True
        for p in matching_plat_alternates:
            cov_obj.parcel_matches.add(*p.plat.parcel_set.all())

    # Lookup by subdivision
    matching_subdivisions = Subdivision.objects.filter(workflow=cov_obj.workflow, name_standardized=plat_name_standardized)
    matching_subdivision_alternates = SubdivisionAlternateName.objects.filter(workflow=cov_obj.workflow, alternate_name_standardized=plat_name_standardized)

    if matching_subdivisions.count() > 0:
        cov_obj.bool_parcel_match = True
        for p in matching_subdivisions:
            cov_obj.parcel_matches.add(*p.parcel_set.all())

    # Lookup by alternate name
    elif matching_subdivision_alternates.count() > 0:
        cov_obj.bool_parcel_match = True
        for p in matching_subdivision_alternates:
            cov_obj.parcel_matches.add(*p.subdivision.parcel_set.all())
