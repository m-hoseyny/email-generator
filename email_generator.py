import pandas as pd
import datetime
from tqdm import tqdm

COLUMNS = {
    'Subjects of Interest': 'Subjects of Interest'
}

def get_file_data_list(path):
    with open(path) as f:
        content = f.readlines()
    return [x.strip() for x in content] 

def get_file_data_str(path):
    with open(path, 'r') as file:
        data = file.read()
    return data


def get_subject_materials(subjects):
    subjects_materials = {}
    for subject in subjects:
        subjects_materials[subject] = {}
        subjects_materials[subject]['name'] = subject
        subjects_materials[subject]['kw'] = get_file_data_list('{}/kw.txt'.format(subject))
        subjects_materials[subject]['email'] = get_file_data_str('{}/email.html'.format(subject))

    return subjects_materials


def find_best_subject(interests, subject_materials):
    for subject, materials in subject_materials.items():
        for kw in materials['kw']:
            if kw.lower() in interests.lower():
                return subject
    return 'Default'


def create_email(subject_material, prof_data):
    return 'email'


def read_professors_csv():
    return pd.read_csv('professors_list.csv')


def save_professors_csv(df):
    return df.to_csv('professors_list_result_{}.csv'.format(datetime.datetime.now()))


def analyze_professors(professors, subject_materials):
    professors['email'] = None
    for i, prof in tqdm(professors.iterrows(), desc='analyzing'):
        # print(prof)
        if not prof[COLUMNS['Subjects of Interest']] or prof[COLUMNS['Subjects of Interest']] == 'nan' or not type(prof[COLUMNS['Subjects of Interest']]) is str:
            continue
        interests = prof[COLUMNS['Subjects of Interest']]
        best_subject = find_best_subject(interests, subject_materials)
        subject_material = subject_materials[best_subject]
        professors.loc[0, 'email'] = create_email(subject_material, prof)
        # print('{}: {}'.format(prof['Name'], best_subject))
    return professors


def main():
    subjects = [
        'DataBase',
        'BigData',
        'IoT',
        'Digital',
        'MachineLearning',
        'Default'
    ]
    subject_materials = get_subject_materials(subjects)
    professors = read_professors_csv()
    result = analyze_professors(professors, subject_materials)
    save_professors_csv(result)



if __name__ == '__main__':
    main()

