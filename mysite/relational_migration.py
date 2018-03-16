from app_folder import app_run, db
from app_folder.models import User, UserCache, User_Records, UserActivity, CompanyName, Company, LinkedInRecord, Skill,\
    Job, Education
from datetime import date
# Migrating from text column to relationships

# Backup all Profile Records
profiles = LinkedInRecord.query.all()
profile_data = dict.fromkeys([p.member_id for p in profiles])

def package_positions(record):
    positions = []
    position_keys = ['companyName_', 'companyUrl_', 'start_date_', 'end_date_', 'summary_', 'title_']
    for i in range(3):
        td = dict(companyName=None, companyUrl=None, start_date=None, end_date=None, summary=None, title=None)
        for pk in position_keys:
            ppk = pk.format(i) # lookup key
            val = getattr(record, ppk, None)
            ppkk = ppk.split("_")[0]
            td[ppkk] = val
        if td['end_date'] is None and td['start_date']:
            td['current'] = True
        else:
            td['current'] = False
        positions.append(td)
    return positions


def package_edu(record):
    edu = []
    edu_keys = ['education_study_field', 'education_school', 'education_degree', 'education_start', 'education_end']
    td = dict.fromkeys(edu_keys)
    for ek in edu_keys:
        td[ek] = getattr(record, ek, None)
    edu.append(td)
    return edu

def package_skills(record):
    if record.skills:
        skills = record.skills.split(", ")
        return skills
    else:
        return None


profile_data = []
for p in profiles:
    mid = p.member_id
    positions = package_positions(p)
    edus = package_edu(p)
    skills = package_skills(p)

    td = dict(member_id=mid, positions=positions, edu=edus, skills=skills)
    profile_data.append(td)

def make_job(pd):
    ready_keys = ['current', 'job_title', 'start_date', 'end_date']
    job_keys = ['current', 'job_title', 'companyName', 'companyUrl', 'companyId', 'start_date', 'end_date',
                'summary']

    job = Job()
    for rk in ready_keys:
        if rk in pd:
            setattr(job, rk, pd[rk])
    db.session.add(job)

    # Associate job with company
    company = lookup_company(pd)
    if not company:
        company = make_company(pd)
    job.company = company
    job.title = pd.get('job_title', None)
    job.start_date = pd.get('start_date', None)
    job.end_date = pd.get('end_date', None)
    job.summary = pd.get('summary', None)
    return job


def lookup_company(pd):
    if 'companyId' in pd:
        company_result = Company.query.filter_by(external_identifiers=int(pd['companyId'])).first()
        if company_result:
            return company_result
        else:
            return None
    else:
        company_name_result = CompanyName.query.filter_by(name=pd['companyName']).first()
        if company_name_result:
            return company_name_result.company
        else:
            return None


def make_company(pd):
    company = Company()
    db.session.add(company)
    if 'companyId' in pd:
        company.external_identifiers = int(pd['companyId'])
    db.session.commit()
    company_name = CompanyName(name=pd['companyName'])
    db.session.add(company_name)
    company.company_names.append(company_name)
    db.session.commit()
    return company


def lookup_skill(sd):
    skill = Skill.query.filter_by(name=sd).first()
    if skill:
        return skill
    else:
        skill = make_skill(sd)
        return skill


def make_skill(sd):
    skill = Skill(name=sd)
    db.session.add(skill)
    return skill


def make_edu(ed):
    if any(ed.values()):
        pass
    else:
        return None

    edu_keys = [('schoolName', 'school'), ('fieldOfStudy', 'study_field'), ('degree', 'degree'),
                ('current', 'current')]

    edu = Education()
    for edu_key in edu_keys:
        if edu_key[0] in ed:
            setattr(edu, edu_key[1], ed[edu_key[0]])

    start_year_ = ed.get('startDateYear', None)
    if start_year_:
        edu.start_year = date(year=start_year_, month=5, day=1)
    end_year_ = ed.get('endDateYear', None)
    if end_year_:
        edu.end_year = date(year=end_year_, month=5, day=1)

    db.session.add(edu)
    return edu

for i, p in enumerate(profile_data):

    # Make positions
    pos_objs = []
    if p['positions']:
        for job in p['positions']:
            pos_objs.append(make_job(job))

    skill_data = []
    if p['skills']:
        for skill in p['skills']:
            skill_data.append(lookup_skill(skill))

    edu_data = []
    if p['edu']:
        for ed in p['edu']:
            eo = make_edu(ed)
            if eo:
                edu_data.append(eo)

    # Get profile record
    lir = LinkedInRecord.query.filter_by(member_id=p['member_id']).first()
    if pos_objs:
        lir.positions.extend(pos_objs)
    if skill_data:
        lir.skills.extend(skill_data)
    if edu_data:
        lir.educations.extend(edu_data)

    db.session.add(lir)
    db.session.commit()

    if i % 10 == 0:
        print("Finished {}".format(i))


