import abc
import pickle

from site_config import FConfig


class SheetMask(abc.ABC):
    """ Accept standard df that will then be masked """

    def __init__(self):
        self.df_ = None
        self.header_mappings = self.load_headers_()

    @property
    @abc.abstractmethod
    def HEADER_FILE(self):
        return None

    @abc.abstractmethod
    def load_headers_(self):
        with open(getattr(FConfig, self.HEADER_FILE), "rb") as hf:
            return pickle.load(hf)

    @abc.abstractmethod
    def do_keeps_(self, df):
        keep_col = self.header_mappings.get('keeps', None)
        if keep_col:
            return df[keep_col]
        else:
            return df

    @abc.abstractmethod
    def do_rename_(self, df):
        renames = self.header_mappings.get('renames', None)
        keep_df = self.do_keeps_(df)
        if renames:
            return keep_df.rename(columns=renames, inplace=True)
        else:
            return keep_df

    @abc.abstractmethod
    def mask_df(self, df):
        masked_df = self.do_rename_(df)
        return masked_df

class JobJetMask(SheetMask):

    @property
    def HEADER_FILE(self):
        return 'HEADERS_JOBJET'

    def __init__(self):
        super().__init__()

    def load_headers_(self):
        return super().load_headers_()

    def do_keeps_(self, df):
        return super().do_keeps_(df)

    def do_rename_(self, df):
        return super().do_rename_(df)

    def mask_df(self, df):
        return super().do_rename_(df)

    def mask_df(self):
        renamed_df = self.do_rename_()
        return renamed_df

