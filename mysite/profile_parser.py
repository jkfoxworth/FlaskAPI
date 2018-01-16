from datetime import date
import re
import json
from operator import itemgetter

class LinkedInProfile(object):
    """
    Class that handles transforming JSON POST Data to Inserting to MySQL DB
    :param raw: JSON Data as received from Flask
    """

    def __init__(self, raw):
        self.raw = raw['data']
        self.member_id = None
        self.name = None
        self.created = None
        self.updated = None
        self.metro = None
        self.postal_code = None
        self.country_code = None
        self.language = None
        self.industry = None
        self.skills = None
        self.summary = None

        self.companyName_0 = None
        self.companyName_1 = None
        self.companyName_2 = None

        self.companyUrl_0 = None
        self.companyUrl_1 = None
        self.companyUrl_2 = None

        self.title_0 = None
        self.title_1 = None
        self.title_2 = None

        self.start_date_0 = None
        self.end_date_0 = None
        self.start_date_1 = None
        self.end_date_1 = None
        self.start_date_2 = None
        self.end_date_2 = None

        self.summary_0 = None
        self.summary_1 = None
        self.summary_2 = None

        self.education_school = None
        self.education_start = None
        self.education_end = None
        self.education_degree = None
        self.education_study_field = None
        self.public_url = None
        self.recruiter_url = None

        self.parse_positions()
        self.parse_profile()

    def parse_positions(self):

        accept_pos_keys = ['companyName', 'summary', 'title', 'startDateYear', 'companyUrl', 'location',
                           'startDateMonth',
                           'companyId', 'endDateMonth', 'endDateYear']

        positions_ = self.raw.get('positions', False)
        if positions_:
            # Accept only 3 positions
            positions = positions_[0:3]
            # Remove the 'referenceCount' key
            positions = [s['position'] for s in positions]
            # Clever? way to match keys and values
            for index, pos in enumerate(positions):
                filtered_pos = {k: v for (k, v) in positions[index].items() if k in accept_pos_keys}
                pos_dict = {'{}_{}'.format(k, index): v for (k, v) in filtered_pos.items()}

                dated_dict = self.date_logic_helper(pos_dict, index)

                # We want to combine start|endDateMonth|Year to one
                # Pass to helper function. Handles updating dictionary

                for k, v in dated_dict.items():


                    self.__dict__[k] = v

    def date_format_helper(self, month, year):

        parsed_date = date(year=year, month=month, day=1)
        return parsed_date

    def date_logic_helper(self, pos_dict, index):
        # Should always have begin date

        startYearString = 'startDateYear_{}'.format(index)
        startMonthString = 'startDateMonth_{}'.format(index)
        endYearString = 'endDateYear_{}'.format(index)
        endMonthString = 'endDateMonth_{}'.format(index)

        start_date_year = pos_dict.get(startYearString, False)
        start_date_month = pos_dict.get(startMonthString, False)

        # Replace seperate year, month keys with one
        # Start dates
        pos_dict.pop(startYearString)

        # Month may not be present
        if start_date_month is False:
            start_date_month = 1
        else:
            pos_dict.pop(startMonthString)

        pos_dict['start_date_{}'.format(index)] = self.date_format_helper(month=start_date_month, year=start_date_year)

        # If this is current role, we are done. Else we need to do the same for end dates

        if endYearString not in pos_dict:
            return pos_dict

        end_date_year = pos_dict.get(endYearString, False)
        end_date_month = pos_dict.get(endMonthString, False)

        # Pop and replace, again

        pos_dict.pop(endYearString)
        if end_date_month is False:
            end_date_month = 1
        else:
            pos_dict.pop(endMonthString)

        pos_dict['end_date_{}'.format(index)] = self.date_format_helper(month=end_date_month, year=end_date_year)

        return pos_dict

    def parse_profile(self):

        profile_ = self.raw.get('profile', False)
        if profile_:
            self.member_id = profile_.get('memberId')
            self.name = "<first>{}</first> <last>{}</last>".format(profile_.get('firstName', ""),
                                                                   profile_.get('lastName', ""))
            # TODO self.created is it a new record or an update?
            # TODO self.updated

            self.metro = profile_.get('location', None)

            # Use regex for postal code and zip code
            self.parse_location(profile_.get('geoRegionSearchUrl', False))

            # Languages may be 0 or more
            languages = profile_.get('languages', False)
            if languages:
                all_lang = []
                for l in languages:
                    all_lang.append(l.get('languageName', ''))
                self.language = ', '.join(all_lang)

            self.industry = profile_.get('industry', None)

            # Skills may be 0 or more
            skills = profile_.get('skills', False)
            if skills:
                self.skills = ', '.join(skills)

            self.summary = profile_.get('summary', None)

            self.parse_educations(profile_.get('educations', False))

            self.public_url = profile_.get('publicLink', None)

            recruiter_params = profile_.get('findAuthInputModel', False)
            if recruiter_params:
                self.recruiter_url = 'https://www.linkedin.com/recruiter/profile/' + recruiter_params.get('asUrlParam', None)

    def parse_educations(self, educations):
        if educations is False:
            return

        # May be 1 or more
        # Choose most recent

        if len(educations) > 1:
            # If end date not in all, return those without
            if all('endDateYear' in edu for edu in educations) is False:
                current_edu = list(filter(lambda x: 'endDateYear' not in x, educations))
                educations = [current_edu[0]] # Potentially more than 1 match, but choose 1
                # Keep in list form to be compatible with next if statement

        if len(educations) == 1:
            edu = educations[0]
            self.education_school = edu.get('schoolName', None)
            education_start = edu.get('startDateYear', None)

            if education_start:
                self.education_start = date(year=education_start, month=1, day=1)

            education_end = edu.get('endDateYear', None)

            if education_end:
                self.education_end = date(year=education_end, month=1, day=1)

            self.education_degree = edu.get('degree', None)
            self.education_study_field = edu.get('fieldOfStudy', None)

    def parse_location(self, geo_url):
        if geo_url is False:
            return
        postal_re = re.compile("postalCode=[0-9]{5}")
        found_postal = postal_re.findall(geo_url)
        if found_postal:
            post_code = found_postal[0].split("=")[1]
            self.postal_code = post_code

        country_re = re.compile("countryCode=[A-z]+")
        found_country = country_re.findall(geo_url)
        if found_country:
            country_code = found_country[0].split("=")[1]
            self.country_code = country_code
