import re
from datetime import date

class ProfilePruner(object):

    RECORD_IS_OLD = 60

    def __init__(self, urls):
        self.request_urls = urls
        self.reference = None
        self.pruned_urls = []
        self.generate_keys()

    def generate_keys(self):
        ref_dict = {}
        for index, u in enumerate(self.request_urls):
            ref_dict[index] = {'url': u, 'member_id': self.find_member_id(u)}
        self.reference = ref_dict

    def find_member_id(self, url):
        b = re.compile('[0-9]{3,}(?=,)')
        mi = b.findall(url)
        if mi:
            return mi[0]
        else:
            return ''


