from datetime import date
import re


class LinkedInProfile(object):
    """
    Class that handles transforming JSON POST Data to Inserting to MySQL DB
    :param raw: JSON Data as received from Flask
    """

    def __init__(self, raw):
        self._raw = raw['data']
        self.member_id = None
        self.first_name = None
        self.last_name = None
        self.created = None
        self.updated = None
        self.metro = None
        self.postal_code = None
        self.country_code = None
        self.summary = None
        self.language = None
        self.industry = None
        self.first_graduation_date = None  # References first graduation date
        self.public_url = None
        self.recruiter_url = None
        self.isCompanyFollower = None
        self.careerInterests = None

        self.positions = None
        self.skills = None
        self.educations = None

        self.parse_positions()
        self.parse_profile()

    def parse_positions(self):

        accept_pos_keys = ['current', 'companyName', 'summary', 'title', 'startDateYear', 'companyUrl',
                           'location', 'startDateMonth', 'companyId', 'endDateMonth', 'endDateYear']

        positions_ = self._raw.get('positions', False)
        if positions_:
            # Remove the 'referenceCount' key
            positions = [s['position'] for s in positions_]
            position_holder = []

            for index, pos in enumerate(positions):
                filtered_pos = {k: v for (k, v) in positions[index].items() if k in accept_pos_keys}
                dated_dict = self.date_logic_helper(filtered_pos)
                position_holder.append(dated_dict)

            self.positions = position_holder

    @staticmethod
    def date_format_helper(month, year):

        parsed_date = date(year=year, month=month, day=1)
        return parsed_date

    def date_logic_helper(self, pos_dict):

        startYearString = 'startDateYear'
        startMonthString = 'startDateMonth'
        endYearString = 'endDateYear'
        endMonthString = 'endDateMonth'

        start_date_year = pos_dict.get(startYearString, False)
        start_date_month = pos_dict.get(startMonthString, False)

        # Replace separate year, month keys with one
        # Start dates
        if start_date_year is False:
            # Software for the ages... :)
            start_date_year = int(date.today().strftime("%Y"))
        else:
            pos_dict.pop(startYearString)

        # Month may not be present
        if start_date_month is False:
            start_date_month = 1
        else:
            pos_dict.pop(startMonthString)

        pos_dict['start_date'] = self.date_format_helper(month=start_date_month, year=start_date_year)

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

        pos_dict['end_date'] = self.date_format_helper(month=end_date_month, year=end_date_year)

        return pos_dict

    def parse_profile(self):

        profile_ = self._raw.get('profile', False)
        if profile_:
            self.member_id = profile_.get('memberId', None)
            self.first_name = profile_.get('firstName', '')
            self.last_name = profile_.get('lastName', '')
            self.metro = profile_.get('location', None)

            # Use regex for postal code and zip code
            self.parse_location(profile_.get('geoRegionSearchUrl', False))

            # Languages may be 0 or more
            languages = profile_.get('languages', False)
            if languages:
                self.language = ', '.join([l.get('languageName', '') for l in languages])

            self.industry = profile_.get('industry', None)

            # Skills may be 0 or more
            skills = profile_.get('skills', False)
            if skills:
                self.skills = skills

            self.summary = profile_.get('summary', None)

            self.parse_educations(profile_.get('educations', False))

            self.public_url = profile_.get('publicLink', None)

            recruiter_params = profile_.get('findAuthInputModel', False)
            if recruiter_params and 'asUrlParam' in recruiter_params:
                self.recruiter_url = 'https://www.linkedin.com/recruiter/profile/' + recruiter_params['asUrlParam']

            self.isCompanyFollower = profile_.get('isCompanyFollower', False)
            has_career_interests = profile_.get('careerInterests', False)
            if has_career_interests:
                self.careerInterests = True
            else:
                self.careerInterests = False

    def parse_educations(self, educations):

        accept_edu_keys = ['schoolName', 'fieldOfStudy', 'degree', 'startDateYear', 'endDateYear', 'current']

        if educations is False:
            return None

        def past_or_present(edu):
            start = 'startDateYear'
            end = 'endDateYear'

            if start not in edu and end not in edu:
                edu['current'] = False
                return edu
            if start in edu and end not in edu:
                edu['current'] = True
                return edu
            else:
                edu['current'] = False
                return edu

        def filter_keys(edu):
            filtered_edu = {k: v for k, v in edu.items() if k in accept_edu_keys}
            return filtered_edu

        parsed_educations = list(map(past_or_present, educations))

        # Method to determine first graduation date
        previous_edu = [edu for edu in parsed_educations if edu['current'] is False]
        if previous_edu:
            # Check if any have end year
            if any(list(filter(lambda x: 'endDateYear' in x, previous_edu))):
                temp_edu = list(filter(lambda x: 'endDateYear' in x, previous_edu))
                sorted_previous = sorted(temp_edu, key=lambda x: x['endDateYear'])  # Sort for earliest
                previous_edu = sorted_previous[0]  # 0 result will be earliest
                grad_year = previous_edu.get('endDateYear', None)
                if grad_year:
                    self.first_graduation_date = date(year=grad_year, month=5, day=1)

        # Filter out junk keys
        filtered_educations = list(map(filter_keys, parsed_educations))
        return filtered_educations

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
