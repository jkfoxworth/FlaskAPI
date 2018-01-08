from datetime import datetime
from bs4 import BeautifulSoup as bs
import re
import pickle

class LinkedInProfile(object):

    def __init__(self, member_id, raw_html, recruiter_url):
        self.doc = bs(raw_html, 'html.parser')
        self.member_id = member_id
        self.name = None
        self.metro = None
        self.zip_code = None
        self.language = None
        self.industry = None
        self.skills = None
        self.summary = None
        self.work_history = None
        self.education = None
        self.public_url = None
        self.sqlData = None
        self.recruiter_url = recruiter_url
        self.extractContent()
        self.sqlProfile()

    def extractContent(self):

        name = self.doc.find("h1").get_text()
        self.name = name
        print(name)

        metro = self.extractText(self.doc.select("div.profile-info .location.searchable"))
        self.metro = metro
        print(metro)

        zip_code = self.doc.select("div.profile-info .location.searchable a")[0]
        zip_code_search = re.compile(r"postalCode=[0-9]{5}")
        if zip_code:
            location_url = zip_code['href']
            zip_code_lookup = zip_code_search.findall(location_url)[0]
            zip_code = zip_code_lookup.split("=")[-1]
            print(zip_code)
            self.zip_code = zip_code

        self.work_history = self.jobHistory()

        language = self.extractText(self.doc.select("#profile-language .searchable"))
        self.language = language

        industry = self.extractText(self.doc.select(".industry a"))
        self.industry = industry

        skills = self.extractText(self.doc.select(".skill"))
        self.skills = skills

        summary = self.extractText(self.doc.select("#profile-summary .searchable"))
        self.summary = summary

        self.education = self.parseEducation()

        public_url = self.extractText(self.doc.select(".public-profile a"), get_href=True)
        self.public_url = public_url

    def parseEducation(self):
        schools = self.doc.select("#profile-education h4")
        edu_date_range = self.doc.select("#profile-education .date-range")
        edu_degree = self.doc.select("#profile-education h5")

        education = []

        if not schools:
            return {}

        for index, s in enumerate(schools):
            school = self.extractText(s)
            try:
                school_dates = self.extractText(edu_date_range[index])
            except IndexError:
                school_dates = 0
            try:
                edu_degr = self.extractText(edu_degree[index])
            except IndexError:
                edu_degr = 0

            td = {'School': school, 'School_Dates': school_dates, 'Degree': edu_degr}
            education.append(td)

        return education

    def extractText(self, element, **kwargs):

        if kwargs:
            if 'position_select' in kwargs:
                manual_position = kwargs['position_select']
            else:
                manual_position = 0

            manual_element = element[manual_position]
            if 'extract_date' in kwargs:
                manual_text = manual_element.get_text(",").split(",")[0]
            elif 'get_href' in kwargs:
                manual_text = manual_element['href']
            else:
                manual_text = manual_element.get_text()



            return manual_text

        if len(element) == 1:
            if isinstance(element, list):

                return " ".join(element[0].get_text().split())
            else:
                return " ".join(element.get_text().split())
        else:
            element_text = []
            for sub_element in element:
                element_text.append(sub_element.get_text())
            return ', '.join(element_text)


    def strpTimeHelper(self, date_string):
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                  "November", "December"]
        months = set(months)
        includes_months = False
        for m in months:
            if m in date_string:
                includes_months = True
                break
        if includes_months:
            dt = datetime.strptime(date_string, "%B, %Y")
        else:
            dt = datetime.strptime(date_string, "%Y")

        return dt


    def parseDates(self, date_range):

        current_time = datetime.now()

        # Extract years in position
        if 'Present' in date_range:
            end_time = current_time
        else:
            end_time = date_range.split(" – ")[1]
            end_time = self.strpTimeHelper(end_time)

        begin_time = date_range.split(" – ")[0]
        begin_time = self.strpTimeHelper(begin_time)

        # Calculate years from datetime delta

        delta = end_time - begin_time
        days = delta.days
        years = round(days / 365, 1)
        return years

    def jobHistory(self):
        # Number of jobs from length of element
        job_elements = self.doc.select("#profile-experience li.position")

        # Iterate through past_jobs, fetching company, position title, years at role

        work_history = {}

        for index, pj in enumerate(job_elements):
            pj_company = self.extractText(pj.select("h5 a"))
            pj_company_url = self.extractText(pj.select("h5 a"), get_href=True)
            pj_position_title = self.extractText(pj.select("h4 a"))
            pj_date_range = self.extractText(pj.select(".date-range"), extract_date=True)
            pj_description = self.extractText(pj.select(".description.searchable"))

            my_keys = [('Position_{}', pj_position_title), ('Company_{}', pj_company), ('URL_{}', pj_company_url),
                       ('Title_{}', pj_position_title), ('Dates_{}', pj_date_range), ('Description_{}', pj_description)]

            these_keys = [(m[0].format(index), m[1]) for m in my_keys]

            for kv in these_keys:
                work_history[kv[0]] = kv[1]

        return work_history

    def sqlProfile(self):
        sql_name = self.name
        sql_metro = self.metro
        sql_zipcode = self.zip_code
        sql_language = self.language
        sql_industry = self.industry
        sql_skills = self.skills
        sql_summary = self.summary
        sql_work_history = pickle.dumps(self.work_history)
        sql_education = pickle.dumps(self.education)
        sql_public_url = self.public_url
        sql_recruiter_url = self.recruiter_url.split("?")[0]

        saved_profile = {'member_id': self.member_id,
                         'name': sql_name,
                         'metro': sql_metro,
                         'zip_code': sql_zipcode,
                         'language': sql_language,
                         'industry': sql_industry,
                         'skills': sql_skills,
                         'summary': sql_summary,
                         'company_0': self.work_history['Company_0'],
                         'company_url_0': self.work_history['URL_0'],
                         'title_0': self.work_history['Title_0'],
                         'dates_0': self.work_history['Dates_0'],
                         'description_0': self.work_history['Description_0'],
                         'company_1': self.work_history['Company_1'],
                         'company_url_1': self.work_history['URL_1'],
                         'title_1': self.work_history['Title_1'],
                         'dates_1': self.work_history['Dates_1'],
                         'description_1': self.work_history['Description_1'],
                         'company_2': self.work_history['Company_2'],
                         'company_url_2': self.work_history['URL_2'],
                         'title_2': self.work_history['Title_2'],
                         'dates_2': self.work_history['Dates_2'],
                         'description_2': self.work_history['Description_2'],
                         'work_history': sql_work_history,
                         'education': sql_education,
                         'public_url': sql_public_url,
                         'recruiter_url': sql_recruiter_url
                         }

        self.sqlData = saved_profile