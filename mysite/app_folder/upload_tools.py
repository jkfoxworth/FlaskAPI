import abc
import os
import re

import pandas as pd
from werkzeug.utils import secure_filename

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











