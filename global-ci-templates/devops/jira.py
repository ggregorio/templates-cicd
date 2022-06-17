import os
import sys

import requests
from requests.auth import HTTPBasicAuth
from termcolor import colored

JIRA_URL = os.environ.get('JIRA_URL')  # Lee las variables del CI/CD
JIRA_USER = os.environ.get('JIRA_USERNAME')  # Lee las variables del CI/CD
JIRA_PASS = os.environ.get('JIRA_PASSWORD')  # Lee las variables del CI/CD


# Solo agrega en projecto de Jira, los nuevos miembros sin borrar los anteriores
def addaprobador(cmdb, array_legajos):
    aprobador = obtenerrolaprobador(cmdb, "Aprobador")
    id_admin = obtenerrolaprobador(cmdb, "Administrators")
    verificaradmin(id_admin, cmdb, array_legajos)
    listafinal = aprobadorcargado(aprobador, cmdb, array_legajos)
    if listafinal:
        request_app = {
            "user": listafinal
        }
        response = requests.post(
            '{}/rest/api/2/project/{}/role/{}'.format(JIRA_URL, cmdb, aprobador),
            auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
            json=request_app,
            verify=False)

        if 200 <= response.status_code < 300:
            print(
                "Se configuro los siguientes legajos {} en el proyecto  Jira {}".format(listafinal,
                                                                                        cmdb))
        else:
            print("No se pudo cargar los actores en el proyecto Jira {}".format(cmdb))
    else:
        print("Todos los aprobadores ya están cargados")


# Devuelve una lista con los sponsors que se deben agregar, si están todos retorna lista vacia
# desde jira
def aprobadorcargado(rolid, cmdb, array_legajos):
    endpoint = '{}/rest/api/2/project/{}/role/{}'.format(JIRA_URL, cmdb, rolid)
    users = requests.get(endpoint,
                         auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
                         verify=False)

    lista_final = []
    agregados = []
    if 200 <= users.status_code < 300:
        for legajo in users.json()["actors"]:
            agregados.append(legajo["name"])

        for legajo in array_legajos:
            if legajo not in agregados:
                lista_final.append(legajo)

        return lista_final
    else:
        print("Se Produjo un error al obtener los roles del proyecto {}".format(cmdb))


# Verifica quien es administrador del proyector en Jira
def verificaradmin(roladm, cmdb, array_legajos):
    endpoint = '{}/rest/api/2/project/{}/role/{}'.format(JIRA_URL, cmdb, roladm)
    users = requests.get(endpoint,
                         auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
                         verify=False)

    lista_final = []
    administradores = []
    if 200 <= users.status_code < 300:
        for legajo in users.json()["actors"]:
            administradores.append(legajo["name"])

        for legajo in array_legajos:
            if legajo in administradores:
                print(colored("El legajo {} es administrador del proyecto {}".format(legajo, cmdb),
                              'red'))
        return lista_final
    else:
        print("Se Produjo un error al obtener los roles del proyect {}".format(cmdb))


# Obtiene el ID de un rol ( Administrators , Aprobador ) desde Jira
def obtenerrolaprobador(cmdb, rol_buscado):
    response = requests.get('{}/rest/api/2/role'.format(JIRA_URL),
                            auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
                            verify=False)

    if 200 <= response.status_code < 300:
        jira_project_response = response.json()
        for project in jira_project_response:
            if project["name"] == rol_buscado:
                return project["id"]
    else:
        print("No se pudieron obtener los Roles de Jira {}".format(cmdb))


# Este Método deja en jira solo los aprobadores que recibe
def setaprobador(cmdb, array_legajos):
    aprobador = obtenerrolaprobador(cmdb, "Aprobador")
    id_admin = obtenerrolaprobador(cmdb, "Administrators")
    verificaradmin(id_admin, cmdb, array_legajos)
    request_app = {
        "categorisedActors": {
            "atlassian-user-role-actor": array_legajos

        }
    }
    response = requests.put('{}/rest/api/2/project/{}/role/{}'.format(JIRA_URL, cmdb, aprobador),
                            auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
                            json=request_app,
                            verify=False)

    if 200 <= response.status_code < 300:
        print("Se configuro los siguientes legajos {} en el proyecto  Jira {}".format(array_legajos,
                                                                                      cmdb))
    else:
        print("No se pudo cargar los actores en el proyecto Jira {}".format(cmdb))


# Obtengo la información del proyecto
def get_jira_project(jira_project):
    try:
        response = requests.get('{}/rest/api/2/project/{}'.format(JIRA_URL, jira_project),
                                auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
                                verify=False)

        if 200 <= response.status_code < 300:
            return response.json()
        else:
            jira_project_response = response.json()
            print(jira_project_response["errorMessages"])
            return ''
    except Exception:
        print("###DevOps Message: Surgio inconveniente al obtener data del proyecto:")
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))
        return ''


# Obtengo todos los proyectos
def get_all_jira_project():
    try:
        response = requests.get('{}/rest/api/2/project'.format(JIRA_URL),
                                auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
                                verify=False)

        if 200 <= response.status_code < 300:
            return response.json()
        else:
            jira_project_response = response.json()
            print(jira_project_response["errorMessages"])
            return ''
    except Exception:
        print("###DevOps Message: Surgio inconveniente al obtener data del proyecto:")
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))
        return ''


# Obtiene la historia de un Issue
def get_history_issue(search_issue):
    issue_data = requests.get('{}/rest/api/2/issue/{}?expand=changelog&fields=summary'
                              .format(JIRA_URL, search_issue),
                              auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
                              verify=False)

    if 200 <= issue_data.status_code < 300:
        return issue_data.json()["changelog"]["histories"]
    else:
        return issue_data.json()["errorMessages"]


# Obtengo la licencia de Jira

def get_licence():
    url = "{}rest/api/2/group/member?" \
          "groupname=jira-software-users&expand=users&startAt=0".format(JIRA_URL)
    response = requests.get(url,
                            auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
                            verify=False)

    if 200 <= response.status_code < 300:
        response = response.json()
        available = True
        if response.get('total') == 2000:
            available = False
        licence = {"licence_use": response.get('total'), "available": available}
        return licence
    else:
        print("No se pudo obtener la cantidad de licencias")


# Agrega Miembro a grupo

def add_user_to_group(user_add, groupname):
    info_user = get_user_info_by_legajo(user_add)

    licence = False

    if not info_user['active']:
        msg = "El usuario con nombre {} no tiene la cuenta activa".format(user_add)
        print(msg)
        return msg

    for group in info_user["groups"]["items"]:
        if group["name"] == "jira-software-users":
            licence = True

    if not licence and info_user:
        endpoint: str = '{}rest/api/2/group/user?groupname={}'.format(JIRA_URL, groupname)

        licence_availabe = get_licence()

        json = {
            "name": user_add
        }

        if licence_availabe.get("available"):
            response = requests.post(endpoint,
                                     auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
                                     json=json,
                                     verify=False)
            if 200 <= response.status_code < 300:
                print("Se pudo agregare la licencia al usuario {}".format(user_add))
                return ""
            else:
                response = response.json()["errorMessages"][0]
                print(response)
                return response
        else:
            print("No hay licencias disponibles para agregar miembros")
    else:
        return ""


# Obtiene la información del usuario

def get_user_info_by_legajo(search_user):
    url = "{}rest/api/2/user?username={}&" \
          "expand=groups&expand=applicationRoles".format(JIRA_URL, search_user)
    response = requests.get(url,
                            auth=HTTPBasicAuth(JIRA_USER, JIRA_PASS),
                            verify=False)

    if 200 <= response.status_code < 300:
        response = response.json()
        return response
    else:
        response = response.json()["errorMessages"][0]
        print(response)
        json = {
            "active": False,
            "groups": {
                "items": []
            }
        }
        return json
