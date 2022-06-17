import glob
import os
import sys
import threading
import time
import requests
from funtions import generenic_get

apps_endpoint = 'https://applications-api-devops.apps.ocpprd.ar.bsch/api/v1.0'
validator_endpoint = "https://project-validator-api-devops.apps.ocppaz1.ar.bsch/api/v1." \
                     "0/applications/"


def get_cmdbs():
    all_cmdb = {}

    try:

        all_cmdb = requests.get('{}/applications'.
                                format(apps_endpoint), verify=False).json()["data"]

    except Exception:
        print("Inconveniente al recuperar lista de cmdb")
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))

    return all_cmdb


def get_cmdb_and_program_id(project_cmdb):
    all_cmdb = requests.get('{}/applications'
                            .format(apps_endpoint),
                            verify=False).json()["data"]

    for cmdb in all_cmdb:
        if project_cmdb == cmdb["name"]:
            return cmdb["id"], cmdb["program_id"]


def get_cmdb_members(gcm_project_id, cdmb_name):
    gtt_endpoint = '{}/applications/{}/memberships'. \
        format(apps_endpoint, gcm_project_id)
    return generenic_get(gtt_endpoint, "CMDB {}".format(cdmb_name))


# Obtiene la lista de los aprobadores del Rol HEAD o SPONSOR
# Ejemplo -> get_approvals_list(project_cmdb, "HEAD")

def get_approvals_list(cmdb_and_program_id, search_role):
    approvers_list = []
    program_data = requests.get('{}/programs/{}/memberships'
                                .format(apps_endpoint, cmdb_and_program_id),
                                verify=False).json()
    for member in program_data:
        for role in member["roles"]:
            if role["name"] == search_role:
                approvers_list.append(member["username"])
    return approvers_list


def get_alternate_approvals_list(cmdb_and_program_id, search_role):
    approvers_list = []
    program_data = requests.get('{}/applications/{}/memberships'
                                .format(apps_endpoint, cmdb_and_program_id),
                                verify=False).json()
    for member in program_data:
        for role in member["roles"]:
            if role["name"] == search_role:
                approvers_list.append(member["username"])
    return approvers_list


# Obtengo la lista de WhiteList del validator
def get_whitelist(validator_user, validator_pass):
    endpoint = "{}project_white_list".format(validator_endpoint)

    response = requests.get(endpoint,
                            verify=False,
                            auth=(validator_user, validator_pass),
                            )
    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la WhiteList")


# Agrego un proyecto a la WhiteList del validator
def update_validator(validator_user, validator_pass, reason, project_id):
    body = {
        "Info": [
            {
                "project_id": "{}".format(project_id),
                "Delete": "False",
                "reason": "{}".format(reason)
            }
        ]
    }

    response = requests.put("{}add_update_project_white_list".format(validator_endpoint),
                            auth=(validator_user, validator_pass),
                            json=body,
                            verify=False)

    if 200 <= response.status_code < 300:
        print(" Se agrego con exito el Proyecto a la WhiteList")
    else:
        print(" No se pudo agregar el Proyecto a la WhiteList")


# Limpio la WhiteList sin sacar al grupo datos que siempre esta en WhiteList
def clean_validator(validator_user, validator_pass, reason, project_id):
    body = {
        "Info": [{
            "project_id": "{}".format(project_id),
            "Delete": "True",
            "reason": "{}".format(reason)
        }]
    }
    endpoint = "{}add_update_project_white_list".format(validator_endpoint)
    response = requests.put(endpoint,
                            auth=(validator_user, validator_pass),
                            json=body,
                            verify=False)

    if 200 <= response.status_code < 300:
        print(" Se genero con exito la baja del Proyecto de la WhiteList")
    else:
        print(" No se pudo borrar el Proyecto de la WhiteList")


def execute_threads(threads, total_items_list, max_threads, cooldown):
    print("Starting threads")
    while len(threads) != 0:
        print("*There are " + str(len(threading.enumerate())) + " threads running, " + str(
            len(threads)) + "/" + str(len(total_items_list)) + " remaining")
        if len(threading.enumerate()) < max_threads:
            threads.pop().start()
        else:
            time.sleep(cooldown)

    while len(threading.enumerate()) > 1:
        print("**There are " + str(len(threading.enumerate())) + " threads running, finishing up")
        time.sleep(cooldown)


def create_excel_header(headers_list, result_file):
    encabezado = "{}\t" * len(headers_list)
    encabezado = encabezado.format(*headers_list)
    print(encabezado, file=open(result_file, "w"))


def unified_excel_contents(source_path, files_to_unify, result_file):
    if source_path is not None and files_to_unify and result_file:
        file = open(result_file, "a")
        read_files = sorted(glob.glob(source_path + files_to_unify))
        for f in read_files:
            with open(f, "r") as infile:
                file.write(infile.read())
            if os.path.isfile(f):
                try:
                    print("Borrando archivo {}".format(f))
                    # Borro archivos viejos
                    os.remove(f)
                except OSError:
                    pass
    else:
        print("###DevOps Message: source_path es {} o files_to_unify es {} o result_file es {}"
              .format(source_path, files_to_unify, result_file))


def get_app_programas():
    """ In Parameter: None
        Out Parameter: A json with programas data
        Function: Gets internal programas information from :
        https://applications-api-devops.apps.ocpprd.ar.bsch/api/v1.0/programs
    """
    ptd_branch_endpoint = '{}/programs'. \
        format(apps_endpoint)

    response = requests.get(ptd_branch_endpoint,

                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudieron obtener los programas")


def get_app_head(program_id):
    """ In Parameter: A program ID (XXXX)
        Out Parameter: A json with the users that are head/sponsor or alternates based on program_id id
        Function: Gets user information from the program_id
    """
    ptd_branch_endpoint = '{}/programs/{}'. \
        format(apps_endpoint, program_id)

    response = requests.get(ptd_branch_endpoint, verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudieron obtener los head/sponsors para el grupo id: {}".format(program_id))
