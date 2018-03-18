import abc
import os
import re

import pandas as pd
from werkzeug.utils import secure_filename

from app_folder.models import LinkedInRecord, Contact
from site_config import FConfig

ALLOWED_EXTENSIONS = ['.csv', '.xls', '.xlsx']
TRY_ENCODINGS = ['', 'latin1', 'cp1252', 'iso-8859-1']
UPLOAD_FOLDER = FConfig.UPLOAD_FOLDER


def inject_allowed_ext():
    return dict(allowed_ext=ALLOWED_EXTENSIONS)


class UploadSpreadsheet(object):
    """
    class object to handle heavy lifting of receiving files via upload

    :param request: flask request object
    """

    # TODO Subclass, mixins for email providers
    allowed_extensions = ALLOWED_EXTENSIONS
    try_encodings = TRY_ENCODINGS

    def __init__(self, request):
        self.request = request
        self.request_file = request.files['file']
        self.uploaded_filename = None
        self.uploaded_file = None
        self.status = None

        self.open_file_(request)

    @staticmethod
    def find_file_ext_(request):
        filename = request.files.get('file', None)
        if not filename:
            return None
        _, file_ext = os.path.splitext(filename)
        return file_ext

    def allowed_file_(self, filename):
        ext = self.find_file_ext_(filename)
        if ext in self.allowed_extensions:
            return True
        else:
            self.status = "Extension {} not permitted".format(ext)
            return False

    def open_file_(self, request):

        """
        Function that handles opening the spreadsheet with pandas
        Gets file extension and uses appropriate open method with pandas
        Tries several encodings until opening is successful or ends with fail

        :return: pd.DataFrame() or False if fail to open
        """

        save_path = self.save_upload_(request)
        if not save_path:
            return None
        file_ext = self.find_file_ext_(request)
        if not file_ext:
            return None

        if file_ext == '.csv':
            open_method = pd.read_csv
        elif file_ext == '.xls' or file_ext == '.xlsx':
            open_method = pd.read_excel
        else:
            # No file extension found
            self.status = 'No file extension was found'
            return None

        for encoding in self.try_encodings:
            try:
                if encoding == '':
                    df = open_method(self.uploaded_filename)

                else:
                    df = open_method(self.uploaded_filename, encoding=encoding)
                self.uploaded_file = df
            except:
                if encoding == self.try_encodings[-1]:
                    # Tried all encodings, all failed
                    self.status = "Unable to determine file encoding"
                    return None
                else:
                    continue

    def save_upload_(self, request):

        file = request.files.get('file')
        if not file:
            self.status = "No file received"
            return None
        if file.filename == '':
            self.status = "Your file name is blank"
            return None

        filename = secure_filename(file.filename)

        if self.allowed_file_(filename) is False:
            return None

        # Save file to open later for analysis
        file.save(os.path.join(UPLOAD_FOLDER, filename))

        # Save location
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        return file_path


class ContactSpreadsheet(UploadSpreadsheet, abc.ABC):

    @property
    @abc.abstractmethod
    def HEADER_SEARCH(self):
        return None

    @abc.abstractmethod
    def scan_headers_(self):
        relevant_headers = {k: [] for k in self.HEADER_SEARCH.keys()}

        cols = self.uploaded_file.columns.tolist()
        for data_type, pattern in self.HEADER_SEARCH.items():
            relevant_headers[data_type] = [match.group() for match in [pattern.search(c) for c in cols] if match]

        return relevant_headers

    @abc.abstractmethod
    def scan_data_(self):

        relevant_headers = self.scan_headers_()
        file_data = self.uploaded_file.fillna('').to_dict('records')

        data_records = []

        for row_data in file_data:
            td = {}
            for data_type, header_names in relevant_headers.items():
                td[data_type] = [sv for sv in [v for k, v in row_data.items() if k in header_names] if sv != '']
            data_records.append(td)


class JobJetSpreadsheet(UploadSpreadsheet, ContactSpreadsheet):

    @property
    def HEADER_SEARCH(self):
        return {'email_personal': re.compile(r"(Personal email \(\d\))", flags=re.IGNORECASE),
                'email_work': re.compile(r"(Work email \(\d\))", flags=re.IGNORECASE),
                'website_personal': re.compile("(Website url \(\d\))", flags=re.IGNORECASE),
                'website_linkedin': re.compile("(LinkedIn url \(\d\))", flags=re.IGNORECASE)}

    def __init__(self, request):
        super().__init__(request)
        self.data_ = []
        if self.uploaded_file:
            self.scan_data_()

    @property
    def records(self):
        return self.data_

    @records.getter
    def records(self):
        for d in self.data_:
            yield d


class DataMapper(object):

    def __init__(self, mapped_object):
        self.mapped_object = mapped_object

    @staticmethod
    def public_search_(key):
        user_name = re.search(r"(?<=\/in\/)([A-z]+)", key)
        if user_name:
            return user_name.group()

        alternative_name = re.search(r"(?<=\/pub\/)([A-z]+)", key)
        if alternative_name:
            return alternative_name.group()
        else:
            return None

    KEY_SEARCH = {'recruiter': re.compile(r"(?<=recruiter\/profile\/)([0-9]+)", flags=re.IGNORECASE),
                  'public': public_search_}


    def locate_primary_(self, row_data):
        # Fetch the linkedin_website key from the row_data
        primary_keys = row_data.get('website_linkedin', [])
        if not primary_keys:
            return None
        else:
            primary_keys = self.extract_key_(primary_keys)

        # Check if any keys found
        if not any(primary_keys.values()):
            return None

        # Prefer member_id
        member_id_, public_url_ = primary_keys['member_id'][0], primary_keys['public_url'][0]

        if member_id_:
            record = LinkedInRecord.query.filter_by(member_id_=member_id_).first()
        else:
            record = LinkedInRecord.query.filter(
                LinkedInRecord.public_url_.ilike("%{}".format(public_url_))).first()
        if record:
            return record

        if not record and public_url_:
            record = LinkedInRecord.query.filter(
                LinkedInRecord.public_url_.ilike("%{}".format(public_url_))).first()
            return record


    def extract_key_(self, primary_keys):
        # Either lookup by recruiter member id or url split after /in/
        keys = dict(member_id=[], public_url=[])
        for pk in primary_keys:
            if 'recruiter' in pk:
                member_match = self.KEY_SEARCH['recruiter'].search(pk)
                if member_match:
                    keys['member_id'].append(member_match.group())
            else:
                url_match = self.KEY_SEARCH['public'](pk)
                if url_match:
                    keys['public_url'].append(url_match)

        return keys


    def fetch_record_(self, row_data):

        return self.locate_primary_(row_data)

    def enrich_record_(self, row_data):

        record = self.fetch_record_(row_data)
        if not record:
            return None

        contact_records = []

        for data_type, data_values in row_data.items():

            if not data_values:
                continue
            if 'linkedin' in data_type:
                continue

            # Is it email or website?
            contact_type, contact_range = data_type.split("_")
            if 'email' in contact_type:
                is_email_ = True
                is_website_ = False
            else:
                is_email_ = False
                is_website_ = True

            if 'person' in contact_range:
                is_personal_ = True
            else:
                is_personal_ = False

            for dv in data_values:
                # Make new contact
                crecord = Contact(address=dv, is_email=is_email_, is_personal=is_personal_, is_website=is_website_)
                db.session.add(crecord)
                contact_records.append(crecord)

        record.contacts.extend(contact_records)
        db.session.add(record)
        return record

    def enrich(self):

        data_records = self.mapped_object.records
        enriched_records = [self.enrich_record_(d) for d in data_records]
        return enriched_records

























