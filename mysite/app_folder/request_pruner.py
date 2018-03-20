import re

# TODO Prune based on if profile has changed
# TODO Send additional data from extension to support this

class ProfilePruner(object):

    RECORD_IS_OLD = 60

    def __init__(self, urls):
        self.request_urls = urls
        self.reference = None
        self.pruned_urls = []
        self.generate_keys()

    def __len__(self):
        return len(self.request_urls)

    def __str__(self):
        return "ProfilePruner with {} urls".format(len(self.request_urls))

    def generate_keys(self):
        ref_dict = {}
        for index, u in enumerate(self.request_urls):
            ref_dict[index] = {'url': u, 'member_id': self.find_member_id(u), 'clean_url': self.clean_url(u)}
        self.reference = ref_dict

    def find_member_id(self, url):
        check_auth_scheme = re.compile('[0-9]{3,},PTS,PTS')
        simple_finder = re.compile('[0-9]{3,}(?=,)')
        find_member = re.compile(r'(?<=memberAuth=)[0-9]{3,}')
        pts_auth = check_auth_scheme.findall(url)
        if pts_auth:
            member_id = find_member.findall(url)
            if member_id:
                member_id = member_id[0]
            else:
                member_id = None
            return member_id
        else:
            member_id = simple_finder.findall(url)
            if member_id:
                member_id = member_id[0]
            else:
                member_id = ''
            return member_id

    def clean_url(self, url):
        return url.split("?")[0]

