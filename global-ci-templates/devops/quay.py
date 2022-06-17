import os
import sys

import requests

QUAY_URL = os.environ.get('QUAY_URL')  # Lee las variables del CI/CD
QUAY_API = 'api/v1'
QUAY_ORGANIZATION = 'santandertec'
QUAY_PRIVATE_TOKEN = os.environ.get('QUAY_PRIVATE_TOKEN')
HEADER = {"Authorization": "Bearer {}".format(QUAY_PRIVATE_TOKEN)}


# Obtengo toda la información de imagenes de proyecto
def get_images(project_id, dockerTemplate, path):
    try:
        if dockerTemplate:
            rules_endpoint = "{}{}/repository/{}/{}/tag".format(QUAY_URL, QUAY_API, QUAY_ORGANIZATION,
                                                                path)
        else:
            rules_endpoint = "{}{}/repository/{}/gitlab-projectid-{}/tag".format(QUAY_URL, QUAY_API, QUAY_ORGANIZATION,
                                                                                 project_id)
        get_rules = requests.get(rules_endpoint,
                                 verify=False,
                                 headers=HEADER
                                 )
        if 200 <= get_rules.status_code < 300:
            return get_rules.json()
        else:
            print("No se pudieron obtener los datos de imagenes")
    except Exception:
        print(
            "###DevOps Message: Surgio inconveniente, "
            "por el siguiente motivo:")
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))


# Obtengo toda la información de los tags
def get_images_tags(project_id, dockerTemplate, path):
    try:
        if dockerTemplate:
            rules_endpoint = "{}{}/repository/{}/{}/tag".format(QUAY_URL, QUAY_API, QUAY_ORGANIZATION,
                                                                path)
        else:
            rules_endpoint = "{}{}/repository/{}/gitlab-projectid-{}/tag".format(QUAY_URL, QUAY_API, QUAY_ORGANIZATION,
                                                                                 project_id)
        get_rules = requests.get(rules_endpoint,
                                 verify=False,
                                 headers=HEADER
                                 )
        if 200 <= get_rules.status_code < 300:
            return get_rules.json()
        else:
            print("No se pudieron obtener los tags")
    except Exception:
        print(
            "###DevOps Message: Surgio inconveniente, "
            "por el siguiente motivo:")
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))


# Obtengo toda la información de los manifest
def get_manifest(project_id, dockerTemplate, path, commitSha):
    try:
        if dockerTemplate:
            rules_endpoint = "{}{}/repository/{}/{}/manifest/{}".format(QUAY_URL, QUAY_API,
                                                                        QUAY_ORGANIZATION,
                                                                        path, commitSha)
        else:
            rules_endpoint = "{}{}/repository/{}/gitlab-projectid-{}/manifest/{}".format(QUAY_URL, QUAY_API,
                                                                                         QUAY_ORGANIZATION, project_id,
                                                                                         commitSha)
        get_rules = requests.get(rules_endpoint,
                                 verify=False,
                                 headers=HEADER
                                 )
        if 200 <= get_rules.status_code < 300:
            return get_rules.json()
        else:
            print("No se pudo obtener la información del manifest")
    except Exception:
        print(
            "###DevOps Message: Surgio inconveniente, "
            "por el siguiente motivo:")
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))


# Obtengo toda la información de los manifest
def get_image_vulnerabilities(project_id, dockerTemplate, path, commitSha):
    try:
        if dockerTemplate:
            rules_endpoint = "{}{}/repository/{}/{}/manifest/{}/security?vulnerabilities=true".format(QUAY_URL,
                                                                                                      QUAY_API,
                                                                                                      QUAY_ORGANIZATION,
                                                                                                      path, commitSha)
        else:
            rules_endpoint = "{}{}/repository/{}/gitlab-projectid-{}/manifest/{}/security?vulnerabilities=true".format(
                QUAY_URL, QUAY_API, QUAY_ORGANIZATION, project_id, commitSha)
        get_rules = requests.get(rules_endpoint,
                                 verify=False,
                                 headers=HEADER
                                 )
        if 200 <= get_rules.status_code < 300:
            objeto = get_rules.json()
            if objeto['status'] == 'scanned':
                return get_rules.json()
            elif objeto['status'] == 'failed':
                return 2
            else:
                return 1
        else:
            print("No se pudieron obtener las vulnerabilidades")
    except Exception:
        print(
            "###DevOps Message: Surgio inconveniente, "
            "por el siguiente motivo:")
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))
