import abc
import pickle

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

