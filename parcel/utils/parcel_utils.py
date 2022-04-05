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
    # First, strip "block" and make all lowercase
    # input_str = input_str.lower().lstrip('block ')
    input_str = re.sub('Block ', '', input_str, flags=re.IGNORECASE).lower()

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

    print(f"{input_str}")
    return None, None


def get_parcel_options(subject_obj):
    '''Get all possibilities for this subject that can be attempted to be mapped, and characterize the number of lots found'''
    out_candidates = []
    metadata = {}
    addition = subject_obj.addition
    block, metadata['block'] = get_blocks(subject_obj.block_final)
    lots, metadata['lot'] = get_lots(subject_obj.lot_final)
    if block and lots:
        for lot in lots:
            out_candidates.append(
                {"subject_id": subject_obj.id, "join_string": f"{addition} Block {block} Lot {lot}", "metadata": metadata})
    # print(blocks, block_style)
        return out_candidates, metadata
    return [], metadata
