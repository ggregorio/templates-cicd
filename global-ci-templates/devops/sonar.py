import os
import sys
from math import ceil

import requests
from termcolor import colored

SONAR_USER = os.environ.get('SONAR_USER')
SONAR_URL = os.environ.get('SONAR_URL')
SONAR_PASS = os.environ.get('SONAR_PASS')


def exception_msg():
    print(
        "###DevOps Message: Surgio inconveniente con tu pedido, el motivo fue:")
    traceBack = sys.exc_info()
    typeError = traceBack[0]
    nameError = traceBack[1]
    tracebackError = traceBack[2].tb_frame
    print("{} {} {}".format(typeError, nameError, tracebackError))


def get_licence():
    try:
        url = "{}api/editions/show_license" \
            .format(SONAR_URL)
        licence = requests.get(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
        if 200 <= licence.status_code < 300:
            return licence.json()
        else:
            print(colored("No se pudo obtener la información de la licencia", 'red'))
    except Exception:
        exception_msg()


def get_line_code_value(project_key):
    try:
        url = "{}api/measures/component?component={}&metricKeys={}" \
            .format(SONAR_URL, project_key, 'ncloc')
        json_data = requests.get(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
        if 200 <= json_data.status_code < 300:
            json_data = json_data.json()
            measure = json_data["component"]["measures"]
            if measure:
                new_lines_value = measure[0]["value"]
                return new_lines_value
            else:
                return 0
        else:
            print(colored("No se pudieron obtener la cantidad de lineas", 'red'))
    except Exception:
        exception_msg()


def get_pull_request_branch(project_key):
    try:
        url = "{}api/project_pull_requests/list?project={}" \
            .format(SONAR_URL, project_key)
        json_dataPullRequest = requests.get(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
        if 200 <= json_dataPullRequest.status_code < 300:
            return json_dataPullRequest.json()
        else:
            print(colored("No se pudieron obtener los pull Request Branch", 'red'))
    except Exception:
        exception_msg()


def delete_pull_request_branch(project_key):
    json_dataPullRequest_json = get_pull_request_branch(project_key)
    pullRequests = json_dataPullRequest_json['pullRequests']
    if pullRequests:
        for pullRequest in pullRequests:
            if pullRequest['target'] != 'master':
                print(pullRequest['target'])
                key = pullRequest['key']
                print(key)
                # Borra pull request branch
                try:
                    url = "{}api/project_pull_requests/delete?project={}&pullRequest={}" \
                        .format(SONAR_URL, project_key, key)
                    delete_prb = requests.post(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
                    if 200 <= delete_prb.status_code < 300:
                        print("Se pudo borrar el pull Request Branch")
                    else:
                        print(colored("No se pudo borrar el pull Request Branch", 'red'))
                except Exception:
                    exception_msg()


def delete_project(project_key):
    try:
        url = "{}api/projects/delete?project={}" \
            .format(SONAR_URL, project_key)
        del_proy = requests.post(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
        if 200 <= del_proy.status_code < 300:
            print("Se pudo borrar el Proyecto")
        else:
            print(colored("No se pudo borrar el proyecto", 'red'))
    except Exception:
        exception_msg()


def create_project_backup(project_key):
    try:
        url = "{}api/project_dump/export?key={}".format(SONAR_URL, project_key)
        cpbkp = requests.post(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
        if 200 <= cpbkp.status_code < 300:
            print("BackUp Realizado")
            return cpbkp.json()
        else:
            print(colored("No se pudo realizar el BackUp", 'red'))
            exit(1)
    except Exception:
        exception_msg()


def create_project(project_name, project_key):
    try:
        url = "{}api/projects/create?name={}&project={}".format(SONAR_URL, project_name, project_key)
        cp = requests.post(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
        if 200 <= cp.status_code < 300:
            return cp.json()
        else:
            print(colored("No se pudo crear el proyecto", 'red'))
    except Exception:
        exception_msg()


def import_project_backup(project_name, project_key):
    try:
        create_project(project_name, project_key)
        url = "{}api/project_dump/import?key={}".format(SONAR_URL, project_key)
        cpbkp = requests.post(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
        if 200 <= cpbkp.status_code < 300:
            print("Importación Realizada")
            return cpbkp.json()
        else:
            print(colored(cpbkp.json()["errors"][0]["msg"], 'red'))
    except Exception:
        exception_msg()


def get_branch_list(project_key):
    try:
        url = "http://sonarprod.ar.bsch:9000/api/project_branches/list?project={}" \
            .format(project_key)
        json_dataBranches = requests.get(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
        if 200 <= json_dataBranches.status_code < 300:
            branches = json_dataBranches.json()['branches']
            return branches
        else:
            print(colored("No se pudo obtener las branches", 'red'))
    except Exception:
        exception_msg()


def get_project_component_date_before(date_before):
    try:
        url = "{}api/projects/search?analyzedBefore={}&ps=500&p={}".format(SONAR_URL, date_before, 1)
        proj_cdb = requests.get(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
        if 200 <= proj_cdb.status_code < 300:
            proj_cdb = proj_cdb.json()
            pages = ceil(proj_cdb['paging']["total"] / proj_cdb['paging']["pageSize"])
            components = proj_cdb["components"]
            for page in range(1, pages):
                url = "{}api/projects/search?analyzedBefore={}&ps=500&p={}".format(SONAR_URL, date_before, pages)
                proj_cdb = requests.get(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
                components += proj_cdb.json()["components"]
            return components

        else:
            print(colored("No se pudieron obtener los proyectos", 'red'))
    except Exception:
        exception_msg()


# Delete a non-main branch of a project or application.
def delete_branches(project_key, branch_name):
    try:
        url = "{}api/project_branches/delete?project={}" \
              "&branch={}".format(SONAR_URL, project_key, branch_name)
        del_branch = requests.post(url, verify=False, auth=(SONAR_USER, SONAR_PASS))
        if 200 <= del_branch.status_code < 300:
            print("Se pudo borrar el Branch")
        else:
            print(colored("No se pudo borrar el Branch", 'red'))
    except Exception:
        exception_msg()
