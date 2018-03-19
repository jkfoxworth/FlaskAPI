import abc
import os
import re

import pandas as pd
from werkzeug.utils import secure_filename

from app_folder import db
from app_folder.models import LinkedInRecord, Contact
from site_config import FConfig

ALLOWED_EXTENSIONS = ['.csv', '.xls', '.xlsx']
TRY_ENCODINGS = ['default', 'unicode' 'latin1', 'cp1252', 'iso-8859-1', 'ascii']
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

    def __init__(self, request_file):
        self.request_file = request_file
        self.uploaded_file_path = None
        self.uploaded_file = None
        self.status = None

        self.open_file_()


    def find_file_ext_(self):
        filename = self.request_file.filename
        if not filename:
            return None
        _, file_ext = os.path.splitext(filename)
        return file_ext

    def allowed_file_(self):
        ext = self.find_file_ext_()
        if ext in self.allowed_extensions:
            return True
        else:
            self.status = "Extension {} not permitted".format(ext)
            return False

    def save_upload_(self):

        file = self.request_file
        if not file:
            self.status = "No file received"
            return None
        if file.filename == '':
            self.status = "Your file name is blank"
            return None

        filename = secure_filename(file.filename)

        if self.allowed_file_() is False:
            return None

        # Save file to open later for analysis
        file.save(os.path.join(UPLOAD_FOLDER, filename))

        # Save location
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        return file_path

    def open_file_(self):

        """
        Function that handles opening the spreadsheet with pandas
        Gets file extension and uses appropriate open method with pandas
        Tries several encodings until opening is successful or ends with fail

        :return: pd.DataFrame() or False if fail to open
        """

        self.uploaded_file_path = self.save_upload_()
        if not self.uploaded_file_path:
            print(self.status)
            return None
        file_ext = self.find_file_ext_()
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
                if encoding == 'default':
                    df = open_method(self.uploaded_file_path)

                else:
                    df = open_method(self.uploaded_file_path, encoding=encoding)
                self.uploaded_file = df
                break
            except Exception as e:
                print(e)
                if encoding == self.try_encodings[-1]:
                    # Tried all encodings, all failed
                    self.status = "Unable to determine file encoding"
                    return None
                else:
                    continue


class ContactSpreadsheet(abc.ABC, UploadSpreadsheet):

    @property
    @abc.abstractmethod
    def HEADER_SEARCH(self):
        return None

    @property
    @abc.abstractmethod
    def KEEP_PATTERNS(self):
        return []

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
                td[data_type] = [sv for sv in [v for k, v in row_data.items() if k in header_names] if self.filter_data_(sv, data_type)]
            data_records.append(td)
        return data_records

    @abc.abstractmethod
    def filter_data_(self, sv, data_type):
        if sv == '':
            return None
        if not self.KEEP_PATTERNS:
            return True
        for kept in self.KEEP_PATTERNS:
            if kept['in'] in data_type and kept['pattern'] is False:
                return True
            for kept_type in kept['in']:
                if kept_type not in data_type:
                    continue
                if kept['pattern'].search(sv) is not None:
                    return True
        return False


class JobJetSpreadsheet(ContactSpreadsheet):

    @property
    def HEADER_SEARCH(self):
        return {'email_personal': re.compile(r"(Personal email \(\d\))", flags=re.IGNORECASE),
                'email_work': re.compile(r"(Work email \(\d\))", flags=re.IGNORECASE),
                'website_personal': re.compile("(Website url \(\d\))", flags=re.IGNORECASE),
                'website_linkedin': re.compile("(LinkedIn url \(\d\))", flags=re.IGNORECASE),
                'member_id': re.compile(r"(Tag1)", flags=re.IGNORECASE)}

    @property
    def KEEP_PATTERNS(self):
        return [{'pattern': False, 'in': ['email']},
                {'pattern': re.compile(r"(linkedin)|(github)|(twitter)|(google)|(facebook)", flags=re.IGNORECASE),
                 'in': ['website']}]

    def __init__(self, request):
        super().__init__(request)
        self.data_ = []
        if self.uploaded_file is not None:
            self.scan_data_()

    @property
    def records(self):
        return self.data_

    @records.getter
    def records(self):
        return self.data_

    def scan_data_(self):
        data_records = super().scan_data_()
        self.data_ = data_records

    def scan_headers_(self):
        relevant_headers = super().scan_headers_()
        return relevant_headers

    def filter_data_(self, sv, data_type):
        return super().filter_data_(sv, data_type)


class DataMapper(object):

    def __init__(self, mapped_object):
        self.mapped_object = mapped_object

    def fetch_record_(self, row_data):
        member_id = row_data.get('member_id', None)
        if not member_id:
            return None

        record = LinkedInRecord.query.get(member_id)
        return record

    def enrich_record_(self, row_data):

        record = self.fetch_record_(row_data)
        if not record:
            return None
        contact_records = []

        for data_type, data_values in row_data.items():

            if not data_values:
                continue
            if 'linkedin' in data_type or 'member_id' in data_type:
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
        if contact_records:
            record.contacts.extend(contact_records)
            db.session.add(record)
            return record
        else:
            return None

    def enrich(self):

        data_records = self.mapped_object.records
        row_count = len(data_records)
        enriched_records = []
        for d in data_records:
            enriched_record = self.enrich_record_(d)
            if enriched_record:
                enriched_records.append(enriched_record)
        return enriched_records, row_count

























