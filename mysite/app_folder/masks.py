import abc
import pickle
import re

from site_config import FConfig


class SheetMask(abc.ABC):
    """ Accept standard df that will then be masked """

    def __init__(self):
        self.renames = None
        self.keeps = None
        self.load_headers_()

    @property
    @abc.abstractmethod
    def HEADER_FILE(self):
        return None

    @abc.abstractmethod
    def load_headers_(self):
        with open(getattr(FConfig, self.HEADER_FILE), "rb") as hf:
            mappings = pickle.load(hf)
            self.keeps = mappings.get('keeps', None)
            self.renames = mappings.get('renames', None)

    @abc.abstractmethod
    def mask_df(self, df):
        df_ = df.copy(deep=True)
        if self.keeps:
            df_.drop([col for col in df_.columns if col not in self.keeps], axis=1, inplace=True)
        if self.renames:
            df_.rename(columns=self.renames, inplace=True)
        return df_

class EnrichEmailMask(SheetMask):

    @property
    @abc.abstractmethod
    def HEADER_FILE(self):
        return None

    @property
    def search_email_col(self):
        return re.compile(r"")

    def load_headers_(self):
        super().load_headers_()

    @abc.abstractmethod
    def find_email_columns_(self, df):
        em = re.compile(r"(home)(.+)(email)", flags=re.IGNORECASE)
        keeps = []
        for c in df.columns:
            m = em.search(c)
            if m:
                keeps.append(c)
        return keeps

    @abc.abstractmethod
    def find_linkedin_columns_(self, df):
        em = re.compile(r"(linkedin)", flags=re.IGNORECASE)
        keeps = []
        for c in df.columns:
            m = em.search(c)
            if m:
                keeps.append(c)
        return keeps

    @abc.abstractmethod
    def row_conditions_(self, df):
        email_columns, linkedin_columns = self.find_email_columns_(df), self.find_linkedin_columns_(df)
        view = df.copy()
        view.fillna("", inplace=True)

        def get_empties(row, columns, inverse=False):
            if inverse:
                return all([row[c]] != '' for c in columns)
            else:
                return all([row[c]] == '' for c in columns)

        view = view.loc[(view.apply(lambda x: get_empties(x, email_columns), axis=1)) &
                        (view.apply(lambda x: get_empties(x, linkedin_columns), axis=1))]

        return view

    def mask_df(self, df):
        conditional_df = self.row_conditions_(df)
        return super().mask_df(conditional_df)


class JobJetMask(SheetMask):

    @property
    def HEADER_FILE(self):
        return 'HEADERS_JOBJET'

    def __init__(self):
        super().__init__()

    def load_headers_(self):
        return super().load_headers_()

    def mask_df(self, df):
        masked_df = super().mask_df(df)
        return masked_df

