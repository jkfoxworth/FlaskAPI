import base64
import io
import pickle
import re

import pandas as pd

from site_config import FConfig

def db_to_df(data, rename_web=True):
    # TODO Remove rename_web, change to AvatureMask
    with open(FConfig.COUNTRY_DICT, "rb") as cc:
        country_dict = pickle.load(cc)
    with open(FConfig.ZIP_DICT, "rb") as zd:
        zip_dict = pickle.load(zd)

    df = pd.DataFrame(data)
    df2 = pd.DataFrame(columns=['DupCheck', 'Hermes ID', 'Full Name', 'First Name', 'Last Name', 'Metropolitan Area',
                                'Home State', 'Home Postal Code', 'Home Country', 'Theater', 'Skills and Technologies',
                                'Company', 'Position Title', 'Prior Employer', 'Prior Position Title',
                                'Work History - Company', 'Work History - Position title', 'Home Email_0',
                                'Home Email_1', 'Home Email_2', 'Home Email_3', 'Work Email_0',
                                'Mobile Phone', 'Home Phone', 'Work Phone', 'Open To Opportunities', 'Company Follower',
                                'Graduation Date or Expected Graduation Date', 'Summary', 'Website_LinkedIn', 'Website_Personal_0', 'Source',
                                'Base64-encoded attachment Name', 'Base64-encoded attachment content'])
    df2['Hermes ID'] = df['member_id']
    df2['Full Name'] = df['first_name'] + " " + df['last_name']
    df2['First Name'] = df['first_name']
    df2['Last Name'] = df['last_name']
    df2['Metropolitan Area'] = df['metro']
    post_int = df['postal_code'].apply(lambda x: to_int(x))
    df2['Home State'] = post_int.apply(lambda x: zip_dict.get(x, ''))
    del post_int
    df2['Home Postal Code'] = df['postal_code'].astype(str).apply(lambda x: x.zfill(5))
    df2['Home Country'] = df['country_code'].apply(lambda x: country_dict.get(x, ''))  # Use country code dict
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
    df2['Website_Linkedin'] = df['public_url']
    df2['Resume'] = df.apply(make_resume, axis=1)
    df2['Hermes Resume'] = df['member_id'].apply(lambda x: make_hermes_link(x))
    df2['Base64-encoded attachment Name'] = df['member_id'] + ".rtf"
    df2['Base64-encoded attachment content'] = df.apply(make_resume_b64, axis=1)

    # Add Contact Data
    # If column not present in df, return '' filled column
    def col_else_blank(target_df, col_name):
        if col_name in target_df.columns:
            return target_df[col_name]
        else:
            return ''

    df2['Home Email_0'] = col_else_blank(df, 'email_home_0')
    df2['Home Email_1'] = col_else_blank(df, 'email_home_1')
    df2['Home Email_2'] = col_else_blank(df, 'email_home_2')
    df2['Work Email_0'] = col_else_blank(df, 'email_work_0')
    df2['Website_Personal_0'] = col_else_blank(df, 'website_personal_0')

    # Remove _(single_int) from Header Names
    def strip_col_index(x):
        ind_search = re.compile(r"(_\d)")
        return ind_search.sub("", x)

    def dupcheck_search(row):
        def website_uid(x):
            s = re.compile(r"(\/in\/)|(\/pub\/)")
            x = s.sub("|", x)
            if '|' in x:
                return x.split("|")[-1]
            else:
                return x

        exacts = [col for col in df2.columns if 'email' in col.lower()]
        sites = [col for col in df2.columns if 'website' in col.lower()]
        site_val = [row_value for row_value in [row[scol] for scol in sites]]
        unexacts = list(map(lambda x: website_uid(x), site_val))
        quoted_search = ["\"{}\"".format(row_value) for row_value in [row[ecol] for ecol in exacts]
                         if len(row_value) > 1]
        unquoted_search = ["\"{}\"".format(row_value) for row_value in unexacts if len(row_value) > 1]

        if not quoted_search and not unquoted_search:
            return ''
        if quoted_search:
            search_string = quoted_search
            if unquoted_search:
                search_string.extend(unquoted_search)
        else:
            if unquoted_search:
                search_string = unquoted_search
        if search_string:
            return " OR ".join(search_string)
        else:
            return ""

    df2.fillna('', inplace=True)
    df2['DupCheck'] = df2.apply(lambda x: dupcheck_search(x), axis=1)

    # Add Contact Data
    # If column not present in df, return '' filled column
    def col_else_blank(target_df, col_name):
        if col_name in target_df.columns:
            return target_df[col_name]
        else:
            return ''

    df2['Home Email_0'] = col_else_blank(df, 'email_home_0')
    df2['Home Email_1'] = col_else_blank(df, 'email_home_1')
    df2['Home Email_2'] = col_else_blank(df, 'email_home_2')
    df2['Work Email_0'] = col_else_blank(df, 'email_work_0')
    df2['Website_Personal_0'] = col_else_blank(df, 'website_personal_0')

    # Remove _(single_int) from Header Names
    def strip_col_index(x):
        ind_search = re.compile(r"(_\d)")
        return ind_search.sub("", x)

    df2.columns = map(strip_col_index, df2.columns)
    if rename_web:
        df2.rename(columns={'Website_LinkedIn': 'Website', 'Website_Personal': 'Website'}, inplace=True)

    return df2

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
    return base64.b64encode(resume.encode()).decode('ascii')


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
    return 'https://estasney1.pythonanywhere.com/resumes/{}'.format(x)

def to_int(x):
    try:
        x = int(x)
        return x
    except ValueError:
        return 0

def db_to_xlsx(data, masker=None, rename_web=True):
    df = db_to_df(data, rename_web)
    del data
    if masker:
        df = masker.mask_df(df)
    xlsx_data = df_to_xlsx(df)
    return xlsx_data

def df_to_xlsx(df):
    """
    Handles conversion of dataframe to excel
    Uses xlsxwriter to apply zip code formatting

    :param df: pandas dataframe
    :return: binary, xlsx data
    """
    output = io.BytesIO()

    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    postal_format = workbook.add_format({'num_format': '00000'})
    worksheet.set_column('F:F', None, postal_format)
    writer.close()
    del writer

    # Seek to beginning of stream
    output.seek(0)
    return output

