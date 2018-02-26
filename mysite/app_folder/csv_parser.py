import base64
import pickle

import pandas as pd


def db_to_csv(data):
    # with open(r"/home/estasney1/mysite/app_folder/country_codes.pkl", "rb") as cc:
    #     country_dict = pickle.load(cc)
    with open(r"C:\Users\estasney\PycharmProjects\FlaskAPIWeb\mysite\app_folder\country_codes.pkl", "rb") as cc:
        country_dict = pickle.load(cc)
    df = pd.DataFrame(data)
    df2 = pd.DataFrame(columns=['Full Name', 'First Name', 'Last Name', 'Metropolitan Area',
                                'Home State', 'Home Postal Code', 'Home Country', 'Theater', 'Skills and Technologies',
                                'Company', 'Position Title', 'Prior Employer', 'Prior Position Title',
                                'Work History - Company', 'Work History - Position title', 'Home Email', 'Work Email',
                                'Mobile Phone', 'Home Phone', 'Work Phone', 'Open To Opportunities', 'Company Follower',
                                'Graduation Date', 'Summary', 'Website', 'Source',
                                'Base64-encoded attachment Name', 'Base64-encoded attachment content'])
    df2['Full Name'] = df['first_name'] + " " + df['last_name']
    df2['First Name'] = df['first_name']
    df2['Last Name'] = df['last_name']
    df2['Metropolitan Area'] = df['metro']
    df2['Home Postal Code'] = df['postal_code'].astype(str)
    df2['Home Country'] = df['country_code'].apply(lambda x: country_dict[x])  # Use country code dict
    df2['Skills and Technologies'] = df['skills']
    df2['Company'] = df['companyName_0']
    df2['Position Title'] = df['title_0']
    df2['Prior Employer'] = df['companyName_1']
    df2['Prior Position Title'] = df['title_1']
    df2['Work History - Company'] = df['companyName_2']
    df2['Work History - Position title'] = df['title_2']
    df2['Open To Opportunities'] = df['careerInterests'].apply(lambda x: boolean_to_string(x))
    df2['Company Follower'] = df['isCompanyFollower'].apply(lambda x: boolean_to_string(x))
    df2['Graduation Date or Expected Graduation Date'] = df['first_graduation_date']
    df2['Summary'] = df['summary']
    df2['Website'] = df['public_url']
    df2['Resume'] = df.apply(make_resume, axis=1)
    df2['Hermes Resume'] = df['member_id'].apply(lambda x: make_hermes_link(x))
    df2['Base64-encoded attachment Name'] = df['member_id'] + ".rtf"
    df2['Base64-encoded attachment content'] = df.apply(make_resume_b64, axis=1)

    return df2.to_csv(index=False)

# Content


def make_resume_b64(row):
    break_line = "-----------"
    resume = "{first} {last}\r\n{location}\r\nSummary\r\n{summary}\r\n{break_1}\r\n" \
             "Experience\r\n\r\n" \
             "{title_0} at {companyName_0}\r\n" \
             "{start_date_0} - Present\r\n" \
             "{summary_0}\r\n\r\n" \
             "{title_1} at {companyName_1}\r\n" \
             "{start_date_1} - {end_date_1}\r\n" \
             "{summary_1}\r\n\r\n" \
             "{title_2} at {companyName_2}\r\n" \
             "{start_date_2} - {end_date_2}" \
             "{summary_2}".format(first=row.first_name,location=row.metro, last=row.last_name, summary=row.summary,
                                  break_1=break_line, title_0=row.title_0, companyName_0=row.companyName_0,
                                  start_date_0=row.start_date_0, summary_0=row.summary_0, title_1=row.title_1,
                                  companyName_1=row.companyName_1, start_date_1=row.start_date_1,
                                  end_date_1=row.end_date_1, summary_1=row.summary_1, title_2=row.title_2,
                                  companyName_2=row.companyName_2, start_date_2=row.start_date_2,
                                  end_date_2=row.end_date_2, summary_2=row.summary_2)
    return base64.b64encode(resume.encode())


def make_resume(row):
    break_line = "-----------"
    resume = "{first} {last}\r\n{location}\r\nSummary\r\n{summary}\r\n{break_1}\r\n" \
             "Experience\r\n\r\n" \
             "{title_0} at {companyName_0}\r\n" \
             "{start_date_0} - Present\r\n" \
             "{summary_0}\r\n\r\n" \
             "{title_1} at {companyName_1}\r\n" \
             "{start_date_1} - {end_date_1}\r\n" \
             "{summary_1}\r\n\r\n" \
             "{title_2} at {companyName_2}\r\n" \
             "{start_date_2} - {end_date_2}" \
             "{summary_2}".format(first=row.first_name,location=row.metro, last=row.last_name, summary=row.summary,
                                  break_1=break_line, title_0=row.title_0, companyName_0=row.companyName_0,
                                  start_date_0=row.start_date_0, summary_0=row.summary_0, title_1=row.title_1,
                                  companyName_1=row.companyName_1, start_date_1=row.start_date_1,
                                  end_date_1=row.end_date_1, summary_1=row.summary_1, title_2=row.title_2,
                                  companyName_2=row.companyName_2, start_date_2=row.start_date_2,
                                  end_date_2=row.end_date_2, summary_2=row.summary_2)
    return resume


def boolean_to_string(x):
        if x is True or x.lower() == 'true':
            return 'Yes'
        elif x is False or x.lower() == 'false':
            return 'No'
        elif x is None or x == '':
            return ''

def make_hermes_link(x):
    return 'http://127.0.0.1:5000/resumes/{}'.format(x)
