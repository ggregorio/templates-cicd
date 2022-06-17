import os
import sys
import requests
from termcolor import colored
# from urllib.parse import urlencode
# from nexuscli.api.repository.recipes import *
# import nexuscli

NEXUS_USER = os.environ.get('NEXUS_USER')
NEXUS_URL = os.environ.get('NEXUS_URL')
NEXUS_PASS = os.environ.get('NEXUS_PASS')


def exception_msg():
    print(
        "###DevOps Message: Surgio inconveniente con tu pedido, el motivo fue:")
    traceBack = sys.exc_info()
    typeError = traceBack[0]
    nameError = traceBack[1]
    tracebackError = traceBack[2].tb_frame
    print("{} {} {}".format(typeError, nameError, tracebackError))


def get_all_repositories():
    try:
        url = "{}service/rest/v1/repositories" \
            .format(NEXUS_URL)
        licence = requests.get(url, verify=False, auth=(NEXUS_USER, NEXUS_PASS))
        if 200 <= licence.status_code < 300:
            return licence.json()
        else:
            print(colored("No se pudieron recuperar los repositorios"), 'red')
    except Exception:
        exception_msg()


# Examples
'''
get_repository(apt,hosted,repo_name)
get_repository(apt,proxy,repo_name)
get_repository(bower,group,repo_name)
get_repository(bower,hosted,repo_name)
get_repository(cocoapods,proxy,repo_name)
get_repository(conan,proxy,repo_name)
get_repository(conda,proxy,repo_name)
get_repository(docker,group,repo_name)
get_repository(docker,hosted,repo_name)
get_repository(docker,proxy,repo_name)
get_repository(gitlfs,hosted,repo_name)
get_repository(go,group,repo_name)
get_repository(go,proxy,repo_name)
get_repository(helm,hosted,repo_name)
get_repository(helm,proxy,repo_name)
get_repository(maven,group,repo_name)
get_repository(maven,hosted,repo_name)
get_repository(maven,proxy,repo_name)
get_repository(npm,group,repo_name)
get_repository(npm,hosted,repo_name)
get_repository(npm,proxy,repo_name)
get_repository(nuget,group,repo_name)
get_repository(nuget,hosted,repo_name)
get_repository(nuget,proxy,repo_name)
get_repository(p2,proxy,repo_name),repo_name)
get_repository(pypi,group,repo_name)
get_repository(pypi,hosted,repo_name)
get_repository(pypi,proxy,repo_name)
get_repository(r,group,repo_name)
get_repository(r,hosted,repo_name)
get_repository(r,proxy,repo_name)
get_repository(raw,group,repo_name)
get_repository(raw,hosted,repo_name)
get_repository(raw,proxy,repo_name)
get_repository(rubygems,group,repo_name)
get_repository(rubygems,hosted,repo_name)
get_repository(rubygems,proxy,repo_name)
get_repository(yum,group,repo_name)
get_repository(yum,hosted,repo_name)
get_repository(yum,proxy,repo_name)
'''


def get_repository(technology, repo_type, repo_name):
    try:
        url = "{}service/rest/v1/repositories/{}/{}/{}" \
            .format(NEXUS_URL, technology, repo_type, repo_name)
        repositories = requests.get(url, verify=False, auth=(NEXUS_USER, NEXUS_PASS))
        if 200 <= repositories.status_code < 300:
            return repositories.json()
        else:
            print(colored("No se pudo obtener la información del repositorio indicado", 'red'))
        return None
    except Exception:
        exception_msg()


def create_repository(technology, repo_type, cr_rp_json):
    try:
        url = "{}service/rest/v1/repositories/{}/{}" \
            .format(NEXUS_URL, technology, repo_type)
        create_repo = requests.post(url, json=cr_rp_json,
                                    verify=False, auth=(NEXUS_USER, NEXUS_PASS))
        if 200 <= create_repo.status_code < 300:
            print("Se pudo crear el repositorio ")
        else:
            print(colored("No se pudo crear el repositorio", 'red'))
    except Exception:
        exception_msg()


'''
nexus_config = nexuscli.nexus_config.NexusConfig(username=NEXUS_USER, password=NEXUS_PASS,
                                                 url=NEXUS_URL, x509_verify=True,
                                                 api_version='v1', config_path=None)
nexus_client = nexuscli.nexus_client.NexusClient(config=nexus_config)
all_repo = nexus_client.repositories.list
devops_npm = nexus_client.repositories.get_by_name('devops')


r = RawHostedRepository(
    name='my-repository',
    blob_store_name='default',
    strict_content_type_validation=False,
    write_policy='ALLOW',
)

nexus_client.repositories.create(r)

r = NpmHostedRepository(
    name='my-repository',
    blob_store_name='default',
    strict_content_type_validation=True,
    write_policy='ALLOW',
)
nexus_client.repositories.create(r)
print("pepe")
'''
