import urllib3

from sta_gitlab import *

urllib3.disable_warnings()

JOB_ID = sys.argv[1]
TAG_NAME = sys.argv[2]
GITLAB_USER_NAME = os.environ.get('GITLAB_USER_NAME')


def check():
    rama_main = False
    aprobador_tecnico = False
    tag_data = get_tag(JOB_ID, TAG_NAME)
    if tag_data:
        pipelines = get_pipelines(JOB_ID)
        for pipeline in pipelines:
            if pipeline["sha"] == tag_data["target"]:
                rama_main = True
        user = get_user(GITLAB_USER_NAME, "NAME")["identities"][0]["extern_uid"]\
            .split(",")[0].split("=")[1]
        project_data = get_project(JOB_ID)
        project_cmdb = ''
        if project_data["tag_list"]:
            project_cmdb = project_data["tag_list"][0].split(":", 1)[1]
        cmdb_id = get_cmdb_and_program_id(project_cmdb)[0]
        cmdb_members = get_cmdb_members(cmdb_id, project_cmdb)
        for member in cmdb_members:
            for rol in member["roles"]:
                if "Aprobador técnico" in rol['name']:
                    if user.upper() in member["username"]:
                        aprobador_tecnico = True
        if aprobador_tecnico and rama_main:
            protected_tag(JOB_ID, TAG_NAME)
            return True
        else:
            delete_tag(JOB_ID, TAG_NAME)

            return False
    else:
        return False


print(check())
