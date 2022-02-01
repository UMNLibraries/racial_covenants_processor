import re
import yaml

def parse_labels_question_type(task_num, label_config):
    answer_nodes = []
    label_regex = fr'{task_num}\.answers\.(\d+)\.label'
    for key, value in label_config.items():
        if re.match(label_regex, key):
            slugified_value = value.replace("'", "-").replace(" ", "-").lower()
            answer_nodes.append({
                'key': key,
                'value': value,
                'value_column': f'data.{slugified_value}',  # Use to access answer columns in reducer output csv
                'index': re.match(label_regex, key).group(1)
            })

    return {
        'task_num': task_num,
        'task_type': 'question',
        'question_text': label_config[f"{task_num}.question"],
        'answers': sorted(answer_nodes, key = lambda i: i['index']),
        'answer_columns': [answer['value_column'] for answer in answer_nodes]
    }

def parse_labels_text_type(task_num, label_config):
    return {
        'task_num': task_num,
        'task_type': 'text',
        'question_text': label_config[f"{task_num}.instruction"],
    }

def parse_labels_dropdown_type(task_num, label_config):
    options_regex = fr'{task_num}\.selects\.0\.options\.\*\.(\d+)\.label'

    options = {}
    for key, value in label_config.items():
        if re.match(options_regex, key):
            for hash, option in value.items():
                options[hash] = option

    return {
        'task_num': task_num,
        'task_type': 'dropdown',
        'question_text': label_config[f"{task_num}.instruction"],
        'options': options
    }

def parse_config_yaml(infile):
    '''In order to load data coming back from the reducers, we need to know what columns match which answer. The master config tells us which task/question is which type, and the "Task_labels" yaml has the answers to each question.'''

    # Open list of questions and what type they are
    with open(infile, 'r') as base_file:
        extractor_types = yaml.full_load(base_file)['extractor_config']

    # Open question labels for joining
    with open(infile.replace('Extractor_config_', 'Task_labels_'), 'r') as label_file:
        label_config = yaml.full_load(label_file)
        master_config = []
        # Different question types will have different records in the task labels, so take those one at a time to gather answer options

        # questions
        for task in extractor_types['question_extractor']:
            master_config.append(parse_labels_question_type(task['task'], label_config))

        # text
        for task in extractor_types['text_extractor']:
            master_config.append(parse_labels_text_type(task['task'], label_config))

        # dropdowns
        for task in extractor_types['dropdown_extractor']:
            master_config.append(parse_labels_dropdown_type(task['task'], label_config))

        return master_config