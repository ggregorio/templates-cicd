import urllib3

from nexus import *

urllib3.disable_warnings()

technology = sys.argv[1]
repo_type = sys.argv[2]
repo_name = sys.argv[3]

repository = get_repository(technology, repo_type, repo_name)
if not repository:
    json = {
        "name": repo_name,
        "online": True,
        "storage": {
            "blobStoreName": "default",
            "strictContentTypeValidation": True,
            "writePolicy": "allow_once"
        }
    }
    if technology == "maven":
        maven_setting = {"maven": {
            "versionPolicy": "Release",
            "layoutPolicy": "Permissive"
        }}
        json.update(maven_setting)

    create_repository(technology, repo_type, json)
print("El repositorio {} existe en Nexus".format(repo_name))
