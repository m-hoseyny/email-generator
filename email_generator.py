import pandas as pd
import datetime
from tqdm import tqdm
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import configparser
import json

COLUMNS = {
    'Subjects of Interest': 'Subjects of Interest',
    'Send Email': 'Send Email'
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


def university_name(name):
    if name.split()[0].lower() == 'University':
        return name
    else:
        return 'the ' + name

def intesetes_algo(interests):
    return interests.split()[0].lower()


def create_email(subject_material, prof_data):
    return subject_material['email'].format(
        NAME=prof_data['Name'].split()[-1].capitalize(),
        UNIVERSITY=university_name(prof_data['University']),
        INTERESTED=intesetes_algo(prof_data['Subjects of Interest'])
    )


def read_professors_csv():
    return pd.read_csv('professors_list.csv')


def save_professors_csv(df):
    return df.to_csv('professors_list.csv'.format(datetime.datetime.now()))


def get_email_service(username, password):
    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
    server.ehlo()
    server.login(username, password)
    return server


def attach_files(file_names, best_subject, message):
    for file in file_names:
        part_att = MIMEBase("application", "octet-stream")
        with open(best_subject + '/' + file, "rb") as attachment:
            part_att.set_payload(attachment.read())  
        encoders.encode_base64(part_att)
        part_att.add_header(
            "Content-Disposition",
            f"attachment; filename= {file}",
        )
        message.attach(part_att)
    return message


def send_email(prof, server, my_email):
    message = MIMEMultipart("alternative")
    receiver_email = 'm.hoseyny@ut.ac.ir'
    message["Subject"] = "Fall 2021 prospective student: Need Admission Information"
    message["From"] = my_email
    message["To"] = receiver_email.rstrip().lstrip()
    message = attach_files(['Mohammad_Hosseini_Resume.pdf', 'Transcript.pdf'], prof['best_subject'], message)
    part = MIMEText(prof['Email Text'], "html")
    message.attach(part)
    print('{} ({}) - {}: {}\n{}'.format(prof['Name'], message["To"], message["Subject"], prof['best_subject'], prof['Email Text']))
    if input('Send Email> [Y/n]').lower() == 'n':
        print('Skip')
        return
    server.sendmail(
        my_email, receiver_email, message.as_string()
    )
    print('Email Sent to: {} ({})'.format(prof['Name'], receiver_email))

def send_emails(df, server, my_email, limit=None):
    print("Sending Emails")
    for i, prof in df.iterrows():
        if limit and limit <= i:
            break
        try:
            if str(prof[COLUMNS['Send Email']]).lower() == 'true':
                print('Skip {} ({}): {}'.format(prof['Name'], prof['Email'], 'Sent Before' ) )
                continue
            send_email(prof, server, my_email)
            df.loc[i, COLUMNS['Send Email']] = 'True'
            save_professors_csv(df)
            time.sleep(5)
        except Exception as e:
            print('Error')
            print(e)


def skip_policy(prof):
    if not prof[COLUMNS['Subjects of Interest']] or prof[COLUMNS['Subjects of Interest']] == 'nan' or not type(prof[COLUMNS['Subjects of Interest']]) is str:
        return 'EmptyInterest'
    if str(prof[COLUMNS['Send Email']]).lower() == 'true':
        return 'SentBefore'
    if type(prof['Email Text']) is not int and (len(str(prof['Email Text'])) > 10):
        return 'EmailTextNotEmpty'
    return None


def analyze_professors(professors, subject_materials):
    professors['subject'] = None
    for i, prof in tqdm(professors.iterrows(), desc='analyzing'):
        # print(prof)
        if skip_policy(prof) is not None:
            print('Skip {} ({}): {}'.format(prof['Name'], prof['Email'], skip_policy(prof) ) )
            continue
        interests = prof[COLUMNS['Subjects of Interest']]
        best_subject = find_best_subject(interests, subject_materials)
        subject_material = subject_materials[best_subject]
        professors.loc[i, 'Email Text'] = create_email(subject_material, prof)
        professors.loc[i, 'best_subject'] = best_subject
        # print('{}: {}'.format(prof['Name'], best_subject))
    return professors


def main():
    config = configparser.ConfigParser()
    config.sections()
    config.read('config.ini')
    subjects = json.loads(config.get('subjcets', 'priority'))
    username = config.get('mail', 'email')
    password = config.get('mail', 'password')
    subject_materials = get_subject_materials(subjects)
    professors = read_professors_csv()
    result = analyze_professors(professors, subject_materials)
    if input('Do you wand to continue...[Y/n]').lower() == 'n':
        print('Exiting')
        return
    save_professors_csv(result)
    server = get_email_service(username, password)
    send_emails(result, server, username, limit=None)




if __name__ == '__main__':
    main()

