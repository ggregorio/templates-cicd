import ast
import sys
import requests
import urllib3
urllib3.disable_warnings()


GITLAB_PRIVATE_TOKEN = sys.argv[1]
project_id = ast.literal_eval(sys.argv[2])

HEADER = {'PRIVATE-TOKEN': '{}'.format(GITLAB_PRIVATE_TOKEN)}


def main():
    endpoint = "https://gitlab.ar.bsch/api/v4/projects/{}".format(project_id)

    project_response = requests.get(endpoint,
                                    verify=False,
                                    headers=HEADER
                                    )
    if 200 <= project_response.status_code < 300:
        project_response = project_response.json()
        VALID = False
        if project_response["tag_list"]:
            for tag in project_response["tag_list"]:
                if tag == "GITLAB_REGISTRY":
                    VALID = True
        return VALID
    else:
        print("No pude obtener el Proyecto ({}) Solicitado".format(project_id))

print(main())
