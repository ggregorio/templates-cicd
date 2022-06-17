import base64
import json
import re

import gitlab
from termcolor import colored
from funtions import *
from devops import *

GITLAB_PRIVATE_TOKEN = os.environ.get('GITLAB_TOKEN')
GITLAB_URL = os.environ.get('GITLAB_URL')
GITLAB_API = 'api/v4'

HEADER = {'PRIVATE-TOKEN': '{}'.format(GITLAB_PRIVATE_TOKEN)}

# Conector principal de la Python Gitlab
# Documentación en https://python-gitlab.readthedocs.io/en/stable/api-objects.html
if GITLAB_URL:
    gl = gitlab.Gitlab(GITLAB_URL,
                       private_token=GITLAB_PRIVATE_TOKEN, ssl_verify=False)

# Generando el archivo para backup de las descripciones
file = "UpdateDescription.xls"
msg = "Project\tURL\tOLD Des\tNew Des"
print(msg, file=open(file, "w"))


# Obtiene todos los proyectos de gitlab por medio de la  Python Gitlab
def get_all_project_python_gitlab():
    projects = gl.projects.list(
        all=True, retry_transient_errors=True, archived=False, empty_repo=False, simple=True)
    return projects


# Crea o actualiza las Merge request (MR) approvals para ambientes previos
# Ruta en $GITLAB_URL/project["path_with_namespace"]/edit --> Merge request (MR) approvals

def mr_approvals_dev_stg(mradevstg_project_id, members, onlydev):
    rules_response = get_mr_approvals(mradevstg_project_id)

    users_id_array = []
    for legajo in members:
        datos_legajo = get_user(legajo, "LDAP")
        if datos_legajo:
            user_id = datos_legajo["id"]
            check_or_add_member(mradevstg_project_id, user_id, legajo, False)
            users_id_array.append(user_id)

    rule_dev = False
    rule_stg = False
    for rule in rules_response:
        if rule["name"] == "Team Members - staging" and not onlydev:
            for user in rule["users"]:
                users_id_array.append(user["id"])
            put_mr_approvals(mradevstg_project_id, rule["name"], rule["protected_branches"][0]["id"],
                             users_id_array, rule["id"], "1")
            rule_stg = True
        elif rule["name"] == "Team Members - development":
            for user in rule["users"]:
                users_id_array.append(user["id"])
            put_mr_approvals(mradevstg_project_id, rule["name"], rule["protected_branches"][0]["id"],
                             users_id_array, rule["id"], "1")
            rule_dev = True

    if not rule_dev:
        id_dev = get_protected_branch(mradevstg_project_id, "development")["id"]
        post_mr_approvals(mradevstg_project_id, "Team Members - development", id_dev, users_id_array)
    if not rule_stg and not onlydev:
        id_stg = get_protected_branch(mradevstg_project_id, "staging")["id"]
        post_mr_approvals(mradevstg_project_id, "Team Members - staging", id_stg, users_id_array)


# Crea una nueva regla  para Merge request (MR) approvals con los usuarios indicados
# Ruta en $GITLAB_URL/project["path_with_namespace"]/edit --> Merge request (MR) approvals

def post_mr_approvals(pmr_project_id, name, branch_id, users):
    rules_endpoint = "{}{}/projects/{}/approval_rules".format(GITLAB_URL, GITLAB_API, pmr_project_id)

    r_heads = {
        "name": name,
        "approvals_required": "1",
        "protected_branch_ids": [branch_id],
        "user_ids": users
    }
    hs_rules = requests.post(rules_endpoint,
                             verify=False,
                             json=r_heads,
                             headers=HEADER
                             )
    if 200 <= hs_rules.status_code < 300:
        print("Regla {} Creada".format(name))
    else:
        print("No se pudo crear la regla {} del proyecto solicitado".format(name))


# Obtengo toda la información de las reglas para Merge request (MR) approvals
def get_mr_approvals(gmr_project_id):
    try:
        rules_endpoint = "{}{}/projects/{}/approval_rules".format(GITLAB_URL, GITLAB_API,
                                                                  gmr_project_id)
        get_rules = requests.get(rules_endpoint,
                                 verify=False,
                                 headers=HEADER
                                 )
        if 200 <= get_rules.status_code < 300:
            return get_rules.json()
        else:
            print("No se pudieron obtener las reglas para Merge request (MR) approvals")
    except Exception:
        print(
            "###DevOps Message: Surgio inconveniente al obtener los approval_rules, "
            "por el siguiente motivo:")
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))


# Actualiza una regla  para Merge request (MR) approvals con los usuarios indicados
# Ruta en $GITLAB_URL/project["path_with_namespace"]/edit --> Merge request (MR) approvals

def put_mr_approvals(putmrproject_id, name, branch_id, users, rule, approvals_cant):
    rules_endpoint = "{}{}/projects/{}/approval_rules/{}".format(GITLAB_URL, GITLAB_API, putmrproject_id,
                                                                 rule)

    r_heads = {
        "name": name,
        "approvals_required": approvals_cant,
        "protected_branch_ids": [branch_id],
        "user_ids": [users]
    }
    hs_rules = requests.put(rules_endpoint,
                            verify=False,
                            json=r_heads,
                            headers=HEADER
                            )
    if 200 <= hs_rules.status_code < 300:
        print("Regla {} Actualizada".format(name))
        return False
    else:
        print("No se pudo actualizar la regla {} del proyecto solicitado".format(name))


def put_mr_approvals_required(putmrarproject_id, rule, approvals_cant):
    # status = ''
    # msg_pmrar = ''
    # variable = ''
    approvals_rule_status = {}
    rule_name = ''
    try:
        rule_name = rule["name"]
        rules_endpoint = "{}{}/projects/{}/approval_rules/{}".format(GITLAB_URL, GITLAB_API,
                                                                     putmrarproject_id,
                                                                     rule["id"])
        r_heads = {
            "approvals_required": approvals_cant
        }

        hs_rules = requests.put(rules_endpoint,
                                verify=False,
                                json=r_heads,
                                headers=HEADER
                                )
        if 200 <= hs_rules.status_code < 300:
            msg_pmrar = "Regla {} actualizada {}".format(rule_name, approvals_cant)
            status = 'ok'
        else:
            msg_pmrar = "No se pudo actualizar regla {} con {}".format(rule_name, approvals_cant)
            status = 'not ok'

    except Exception:
        msg_pmrar = "No se pudo hacer put regla {} con {}, por:".format(rule_name, approvals_cant)
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))
        status = 'not ok'
    print(msg_pmrar)
    approvals_rule_status[rule_name] = status
    return approvals_rule_status


# Borro una regla de aprobación

def delete_mr_approvals(dmraproject_id, mr_rule_name, mr_rule_id):
    endpoint = '{}{}/projects/{}/approval_rules/{}' \
        .format(GITLAB_URL, GITLAB_API, dmraproject_id, mr_rule_id)

    update = requests.delete(endpoint,
                             verify=False,
                             headers=HEADER
                             )
    if 200 <= update.status_code < 300:
        print("Se Pudo borrar la regla {}".format(mr_rule_name))
    else:
        print("No se Pudo borrar la regla {}".format(mr_rule_name))


# Obtiene la Push Rule Configurada
def get_push_rules(gprproject_id):
    response = requests.get(
        '{}{}/projects/{}/push_rule'.format(GITLAB_URL, GITLAB_API, gprproject_id),
        headers=HEADER,
        verify=False)
    if 200 <= response.status_code < 300:
        return response.json().get("commit_message_regex")
    else:
        print("No se pudo obtener la Push del proyecto")


# Agrega la Push Rule solictada si tiene mas de una y en caso de no tener agrega la indicada.
# Ruta en gitlab $GITLAB_URL/project["path_with_namespace"]/-/settings/repository --> Push rules

def set_push_rules(project_data, obj_push_rule):
    regex_msg = get_push_rules(project_data["id"])

    if regex_msg == obj_push_rule:
        print("Ya tenia configurada la Push Rule Solicitada")
    else:
        if regex_msg == '':
            push_rule = obj_push_rule
        else:
            search_value = regex_msg.find(obj_push_rule)
            if search_value == -1:
                push_rule = '{}|{}'.format(regex_msg, obj_push_rule)
            else:
                push_rule = regex_msg

        message_data = {
            'commit_message_regex': push_rule
        }

        pre_mod = "El Proyecto ID: {} Nombre: {} tenia configurada la siguiente " \
                  "Push Rule {}".format(project_data.get("id"), project_data.get("name"), regex_msg)

        print(pre_mod)

        response = requests.put('{}/{}/projects/{}/push_rule'
                                .format(GITLAB_URL, GITLAB_API, project_data.get("id")),
                                headers=HEADER,
                                json=message_data,
                                verify=False)
        if 200 <= response.status_code < 300:
            post_mod = "El Proyecto ID: {} Nombre: {} se le configuro la siguiente Push " \
                       "Rule {}".format(project_data.get("id"), project_data.get("name"), push_rule)
            print(post_mod)
        else:
            print("No se pudo configurar la Push rule")


# Borra la protección de la rama solicitada
# Ruta en gitlab $GITLAB_URL/project["path_with_namespace"]/-/settings/repository --> Protected branches

def delete_protect_branches(dpbproject_id, branch):
    endpoint = '{}{}/projects/{}/protected_branches/{}' \
        .format(GITLAB_URL, GITLAB_API, dpbproject_id, branch)

    update = requests.delete(endpoint,
                             verify=False,
                             headers=HEADER
                             )
    if 200 <= update.status_code < 300:
        print("Se Pudo borrar la protección de la rama {}".format(branch))
    else:
        print("No se Pudo borrar la protección de la rama {}".format(branch))


# Crea la protección de la rama solicitada para un proyecto con los aprobadores
# Ruta en gitlab $GITLAB_URL/project["path_with_namespace"]/-/settings/repository --> Protected branches

def post_protect_branch(ppbproject_id, name, array_qa, searchby):
    if name == "master":
        protected_branch_request = {
            "name": name,
            "push_access_level": "0",
            "allowed_to_merge": [],
            "code_owner_approval_required": False
        }
        for legajo in array_qa:
            user_id = get_user(legajo, searchby)
            if user_id:
                user_id = user_id['id']
                check_or_add_member(ppbproject_id, user_id, legajo, False)
                info_user = {'access_level': '40', 'user_id': user_id}
                protected_branch_request["allowed_to_merge"].append(info_user)
    else:
        protected_branch_request = {
            "name": name,
            "push_access_level": "0",
            "merge_access_level": "30",
            "allow_force_push": False,
            "code_owner_approval_required": False
        }

    endpoint = '{}{}/projects/{}/protected_branches' \
        .format(GITLAB_URL, GITLAB_API, ppbproject_id)
    update = requests.post(endpoint,
                           verify=False,
                           json=protected_branch_request,
                           headers=HEADER
                           )

    if 200 <= update.status_code < 300:
        print("Rama {} Protegida".format(name))
    else:
        print("Error en Proteger {}".format(name))


# Flujo de Trabajo que borra las protecciones de todas las ramas y deja master con los QA Lider y
# los ambientes previos con Push "No One" y Merge "Developers + Maintainers"

def protect_branches(pbproject_id, array_qa):
    delete_protect_branches(pbproject_id, "master")
    delete_protect_branches(pbproject_id, "staging")
    delete_protect_branches(pbproject_id, "development")

    post_protect_branch(pbproject_id, "master", array_qa, "USERNAME")
    post_protect_branch(pbproject_id, "development", array_qa, "USERNAME")
    post_protect_branch(pbproject_id, "staging", array_qa, "USERNAME")


# Obtengo la información de una rama protegida
# Ruta en gitlab $GITLAB_URL/project["path_with_namespace"]/-/settings/repository --> Protected branches

def get_protected_branch(gpbproject_id, branch_name):
    ptd_branch_endpoint = '{}{}/projects/{}/protected_branches/{}'. \
        format(GITLAB_URL, GITLAB_API, gpbproject_id, branch_name)

    response = requests.get(ptd_branch_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No Tiene protegida la Rama {}".format(branch_name))
        return None


# Obtengo la lista de los QA Lider en forma username si el 2do parametro esta en true
# Si esta en false voy a devolver una lista de legajos

def get_qa_leaders(gqalproject_id, username):
    qa_list = []
    merge_users = get_protected_branch(gqalproject_id, "master")
    if merge_users:
        merge_users = merge_users["merge_access_levels"]

        for merge_user in merge_users:
            # user = ''
            if merge_user["user_id"]:
                user = get_user(merge_user["user_id"], "ID")
                if username:
                    user_name = user["username"]
                    user = '@' + str(user_name)
                else:
                    legajo_final = user["identities"][0]["extern_uid"]
                    legajo_final = legajo_final.split(",")[0]
                    legajo_final = legajo_final.split("=")[1]
                    user = legajo_final.upper()
                qa_list.append(user)
    return qa_list


# Obtengo la lista de los QA Lider en forma username de la descripción del proyecto

def get_qa_leaders_description(project_data):
    split_description = project_data.get("description").split(".")

    qa_leader = split_description[6]
    qa_leader = qa_leader.replace('@', "")
    qa_leader = qa_leader.replace("QA Leaders: ", "")
    qa_leader = qa_leader.replace(' ', "")
    qa_leader = qa_leader.split(",")

    return qa_leader


# Flujo de Trabajo Para Configurar un QA Lider

def set_qa_leader(sqalproject_id, mantener_qa, array_qa):
    qa_list = array_qa
    if mantener_qa:
        actual_qa = get_qa_leaders(sqalproject_id, False)
        if actual_qa:
            for agregar in actual_qa:
                if agregar.upper() not in qa_list:
                    qa_list.append(agregar.upper())

    delete_protect_branches(sqalproject_id, "master")
    post_protect_branch(sqalproject_id, "master", qa_list, "LDAP")

    # Como borramos la protección de master hay que volver a setear las reglas con este ambiente
    # Obtengo el ID
    branch_master_id = get_protected_branch(sqalproject_id, "master")["id"]
    # Seteo a la regla HEAD y SPONSOR la branch Master
    update_branch_rules_head_sponsor(sqalproject_id, branch_master_id)


# Si la Regla es HEAD o SPONSOR le configura la branch master
# Ruta en $GITLAB_URL/project["path_with_namespace"]/edit --> Merge request (MR) approvals

def update_branch_rules_head_sponsor(ubrhsproject_id, branch_master_id):
    protected_branch = {
        "protected_branch_ids": [branch_master_id]
    }

    rules_response = get_mr_approvals(ubrhsproject_id)

    for rule in rules_response:
        if rule["name"] == "Head" or rule["name"] == "Sponsor":

            rules_endpoint = "{}{}/projects/{}/approval_rules/{}".format(GITLAB_URL, GITLAB_API,
                                                                         ubrhsproject_id, rule["id"])

            hs_rules = requests.put(rules_endpoint,
                                    verify=False,
                                    json=protected_branch,
                                    headers=HEADER
                                    )
            if 200 <= hs_rules.status_code < 300:
                print("Regla {} Actualizada".format(rule["name"]))
            else:
                print("No se pudo actualizar las reglas del proyecto solicitado")


# Obtengo todos los proyectos de gitlab recorriendo las paginas que provee la api

def get_all_project():
    page = 1
    prj_endpoint = '{}{}/projects?per_page=100&sort=desc&page={}'.format(GITLAB_URL, GITLAB_API,
                                                                         page)
    response = requests.get(prj_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        paginas = int(response.headers["X-Total-Pages"])
        all_projects = response.json()

        for page in range(2, paginas):
            page_projects = requests.get(prj_endpoint,
                                         headers=HEADER,
                                         verify=False).json()
            all_projects += page_projects

        return all_projects
    else:
        print("No se pudieron obtener los proyectos")


# Obtengo todos los grupos

def get_all_group():
    print("Obteniendo todos los grupos")
    page = 1
    list_all_project = []
    pg_endpoint = '{}{}/groups?&per_page=100&page={}' \
                  '&order_by=name&sort=asc&archived=False'. \
        format(GITLAB_URL, GITLAB_API, page)

    all_project = requests.get(pg_endpoint,
                               verify=False,
                               headers=HEADER
                               )
    if 200 <= all_project.status_code < 300:
        paginas = int(all_project.headers["X-Total-Pages"])
        for page in range(0, paginas):
            pg_endpoint = '{}{}/groups?&per_page=100&page={}' \
                          '&order_by=name&sort=asc&archived=False'. \
                format(GITLAB_URL, GITLAB_API, page + 1)
            page_projects = requests.get(pg_endpoint
                                         .format(GITLAB_URL, GITLAB_API, page),
                                         headers=HEADER,
                                         verify=False).json()
            list_all_project.extend(page_projects)
        return list_all_project
    else:
        print("No pudieron obtener los datos de los grupos")


# Elimina Grupos

def delete_groups(group_id, group_name):
    endpoint = '{}{}/groups/{}' \
        .format(GITLAB_URL, GITLAB_API, group_id)

    update = requests.delete(endpoint,
                             verify=False,
                             headers=HEADER
                             )
    if 200 <= update.status_code < 300:
        print(colored("Se Pudo borrar el grupo {}".format(group_name),
                      'green'))
    else:
        print(colored("No se Pudo borrar el grupo {}".format(group_name),
                      'red'))


# Obtengo todos los proyectos de un grupo especifico, los archivados no son traidos. Tengo un Maximo de 100 por pagina

def get_projects_group(group_id):
    print("Obteniendo todos los proyectos del grupo")
    page = 1
    list_all_project = []
    pg_endpoint = '{}{}/groups/{}/projects?include_subgroups=True&per_page=100&page={}' \
                  '&order_by=name&sort=asc&archived=False'. \
        format(GITLAB_URL, GITLAB_API, group_id, page)

    all_project = requests.get(pg_endpoint,
                               verify=False,
                               headers=HEADER
                               )
    if 200 <= all_project.status_code < 300:
        paginas = int(all_project.headers["X-Total-Pages"])
        for page in range(0, paginas):
            pg_endpoint = '{}{}/groups/{}/projects?include_subgroups=True&per_page=100&page={}' \
                          '&order_by=name&sort=asc&archived=False'. \
                format(GITLAB_URL, GITLAB_API, group_id, page + 1)
            page_projects = requests.get(pg_endpoint
                                         .format(GITLAB_URL, GITLAB_API, page),
                                         headers=HEADER,
                                         verify=False).json()
            list_all_project.extend(page_projects)
        return list_all_project
    else:
        print("No pudieron obtener los datos del Grupo ID {} Solicitado".format(group_id))


# Obtengo la información del usuario

def get_user(dato, tipo):
    get_user_endpoint = "{}{}/users?id={}".format(GITLAB_URL, GITLAB_API, dato)
    if tipo == "LDAP":
        get_user_endpoint = '{}{}/users?extern_uid=cn={},ou=users,ou=usuarios,ou=central,dc=rio,' \
                            'dc=ar,dc=bsch&provider=ldapmain' \
            .format(GITLAB_URL, GITLAB_API, dato)
    elif tipo == "USERNAME":
        get_user_endpoint = "{}{}/users?username={}".format(GITLAB_URL, GITLAB_API, dato)
    elif tipo == "NAME":
        get_user_endpoint = "{}{}/users?search={}".format(GITLAB_URL, GITLAB_API, dato)

    user = requests.get(get_user_endpoint,
                        verify=False,
                        headers=HEADER
                        ).json()
    if user:
        return dict(user[0])
    else:
        print("No pude obtener los datos del Usuario ({}) Solicitado".format(dato))
        return []


# Obtengo la información de un grupo especifico

def get_group(group_id):
    endpoint = "{}{}/groups/{}".format(GITLAB_URL, GITLAB_API, group_id)

    project_response = requests.get(endpoint,
                                    verify=False,
                                    headers=HEADER
                                    )
    if 200 <= project_response.status_code < 300:
        return project_response.json()
    else:
        print("No pude obtener el Proyecto ({}) Solicitado".format(group_id))


# Obtengo la información de un proyecto especifico

def get_project(getproject_id):
    endpoint = "{}{}/projects/{}".format(GITLAB_URL, GITLAB_API, getproject_id)

    project_response = requests.get(endpoint,
                                    verify=False,
                                    headers=HEADER
                                    )
    if 200 <= project_response.status_code < 300:
        return project_response.json()
    else:
        print("No pude obtener el Proyecto ({}) Solicitado".format(getproject_id))


# Verifico si el usuario es miembro del proyecto si la var Group es False, en caso de no ser lo agregamos
# Si Group es True hace lo mismo para grupos

def check_or_add_member(project_group_id, user_id, legajo, group):
    endpoint = "{}{}/projects/{}/members/{}".format(GITLAB_URL, GITLAB_API, project_group_id,
                                                    user_id)
    rq_endpoint = "{}{}/projects/{}/members".format(GITLAB_URL, GITLAB_API, project_group_id)
    if group:
        endpoint = "{}{}/groups/{}/members/{}".format(GITLAB_URL, GITLAB_API, project_group_id,
                                                      user_id)
        rq_endpoint = "{}{}/groups/{}/members".format(GITLAB_URL, GITLAB_API, project_group_id)

    project_member_response = requests.get(endpoint,
                                           verify=False,
                                           headers=HEADER
                                           )
    if not 200 <= project_member_response.status_code < 300:
        add_member = {
            "access_level": "30",
            "user_id": user_id
        }

        update = requests.post(rq_endpoint,
                               verify=False,
                               json=add_member,
                               headers=HEADER
                               )
        if 200 <= update.status_code < 300:
            print("Se Agrego el Usuario {} al proyecto o grupo".format(legajo))
    else:
        print("El Usuario ({}) Ya es miembro del proyecto o grupo".format(legajo))


# Verifica si existe la rama solicitada y en caso de no estar la crea

def check_or_create_branch(ccbproject_id, branch):
    response = requests.get('{}{}/projects/{}/repository/branches/{}'
                            .format(GITLAB_URL, GITLAB_API, ccbproject_id, branch),
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        print("La Rama {} Existe".format(branch))
        return response.json()
    else:
        new_branch = {
            'branch': branch,
            'ref': "master"
        }
        response = requests.post('{}{}/projects/{}/repository/branches'
                                 .format(GITLAB_URL, GITLAB_API, ccbproject_id),
                                 headers=HEADER,
                                 json=new_branch,
                                 verify=False)
        if 200 <= response.status_code < 300:
            print("Se creo la Rama {}".format(branch))
            return response.json()
        else:
            print("No se pudo crear la rama error {}".format(response.status_code))


# Borra una rama solicitada

def delete_branch(dbproject_id, branch):
    response = requests.delete('{}{}/projects/{}/repository/branches/{}'
                               .format(GITLAB_URL, GITLAB_API, dbproject_id, branch),
                               headers=HEADER,
                               verify=False)

    if 200 <= response.status_code < 300:
        print("La Rama {} fue borrada exitosamente".format(branch))
    else:
        print("No se pudo borrar la rama error {}".format(response.status_code))


# Actualiza un proyecto con el json suministrado

def put_project(json_proj, pjproject_id):
    resp = ''
    try:
        resp = requests.put('{}{}/projects/{}'
                            .format(GITLAB_URL, GITLAB_API, pjproject_id),
                            headers=HEADER,
                            json=json_proj,
                            verify=False)
    except Exception:
        print("Inconveniente al pushear data al proyecto {}".format(pjproject_id))
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))

    return resp


# Flujo de Trabajo que Actualiza las descripciones del proyecto ( Deja Normalizado HEAD,SPONSOR,CMDB,PROGRAMA,QA)
# Configura only_allow_merge_if_pipeline_succeeds a True

def update_project(project_data):
    # Update project description with head and sponsor and qa_leaders

    print("Descripción Antes de Ejecutar")
    pre_des = project_data["description"]
    p_url = "{}{}".format(GITLAB_URL, project_data["path_with_namespace"])
    print(pre_des)

    descripcion_proj = ''
    descripcion_proj = get_description(descripcion_proj, project_data)

    # qa_list = get_qa_leaders(project_data["id"], True)

    if project_data["tag_list"]:
        project_cmdb = project_data["tag_list"][0].split(":", 1)[1]
        '''
        program = ''

        heads_list = get_approvals_list(project_cmdb, "HEAD")
        sponsors_list = get_approvals_list(project_cmdb, "SPONSOR")

        if heads_list:
            heads_list = get_list_gitlab_username(heads_list[0])
        else:
            heads_list = []

        if sponsors_list:
            program = sponsors_list[1]
            sponsors_list = get_list_gitlab_username(sponsors_list[0])

        else:
            sponsors_list = []
            
        new_desciption = '{}. CDMD: {}. ID del Programa: {}. Head : {}. Sponsor: {}. QA Leaders: {}.'.format(
        descripcion_proj, project_cmdb, program,
            ', '.join(heads_list),
            ', '.join(sponsors_list),
            ', '.join(qa_list))
        '''

        new_desciption = '{}. CDMD: {}.'.format(descripcion_proj, project_cmdb)

        update_description = {
            'description': new_desciption,
            'only_allow_merge_if_pipeline_succeeds': True
        }

        resp = put_project(update_description, project_data["id"])

        if not 200 <= resp.status_code < 300:
            ud_msg = "No se actualizo la descripción del proyecto {} ".format(project_data["name"])
            print(ud_msg)
            return 'not ok', ud_msg
        else:
            ud_msg = "Se actualizo correctamente la descripción del proyecto {} ".format(
                project_data["name"])
            print(ud_msg)
            file_msg = "{}\t" * 4
            file_msg = file_msg.format(project_data["name"], p_url, pre_des, new_desciption)
            print(file_msg, file=open(file, "a"))
            return 'ok', ud_msg
    else:
        print("No se actualizo la descripción del proyecto {} porque "
              "no tiene el tag de CMDB ".format(project_data["name"]))
        ud_msg = "No se actualizo la descripción del proyecto {} porque " \
                 "no tiene el tag de CMDB ".format(project_data["name"])
        print(ud_msg)
        return 'not ok', ud_msg


def set_topic_to_project(stproject_id, tag_list, new_topic):
    if new_topic not in tag_list:
        tag_list.append(new_topic)

        topics_json = {
            'tag_list': tag_list
        }
        resp = put_project(topics_json, stproject_id)
        if resp != '':
            if not 200 <= resp.status_code < 300:
                st_msg = "No se pudo pushear topic al proyecto por {}".format(resp.text)
                print(st_msg)
                return 'not ok', st_msg
            else:
                st_msg = "Topic {} agregado al proyecto {} ".format(tag_list, stproject_id)
                print(st_msg)
                return 'ok', st_msg
        else:
            return 'not ok', "No se pudo pushear topic al proyecto"
    else:
        print("New topic {} ya se encuentra en {}".format(new_topic, stproject_id))


def set_pipeline_success_to_project(spsproject_id, allow_merge):
    if allow_merge is not None:

        data_json = {
            'only_allow_merge_if_pipeline_succeeds': allow_merge,
        }
        resp = put_project(data_json, spsproject_id)
        if resp != '':
            if not 200 <= resp.status_code < 300:
                sps_msg = "No se pudo setear el check del allow merge al proyecto por {}".format(
                    resp.text)
                print(sps_msg)
                return 'not ok', sps_msg
            else:
                sps_msg = "Allow merge {} agregado al proyecto {} ".format(allow_merge, spsproject_id)
                print(sps_msg)
                return 'ok', sps_msg
        else:
            return 'not ok', "No se pudo pushear Allow merge al proyecto"
    else:
        print("Parametro vacio -> {}".format(allow_merge))


def get_description(descripcion_proj, project_data):
    if project_data["description"]:
        split_description = project_data["description"].split(".")
        descripcion_proj = split_description[0]
    return descripcion_proj


# Configura la rama por defecto de una branch

def set_default_branch(project_data, default_branch):
    update_description = {
        'default_branch': default_branch
    }

    check_or_create_branch(project_data.get("id"), default_branch)

    resp = put_project(update_description, project_data["id"])

    if not 200 <= resp.status_code < 300:
        print("No se pudo configurar la rama {} a default del proyecto {} ".format(default_branch,
                                                                                   project_data.get(
                                                                                       "name")))
    else:
        print("Se pudo configurar la rama {} a default del proyecto {}  ".format(default_branch,
                                                                                 project_data.get(
                                                                                     "name")))


# Obtengo una lista de todos los username de gitlab

def get_list_gitlab_username(obj_list):
    final_list = []
    for index, user in enumerate(obj_list):
        user = get_user(user, "LDAP")
        if user:
            username = '@' + str(user["username"])
            final_list.append(username)
    return final_list


# Obtengo una lista de todos los userid de gitlab

def get_list_gitlab_userid(obj_list):
    final_list = []
    for index, user in enumerate(obj_list):
        user = get_user(user, "LDAP")
        if user:
            final_list.append(user["id"])
    return final_list


# Obtengo todas las variables de un grupo

def get_group_variables(project_group_id):
    endpoint = "{}{}/groups/{}/variables".format(GITLAB_URL, GITLAB_API, project_group_id)

    var_group = requests.get(endpoint,
                             verify=False,
                             headers=HEADER
                             )
    if 200 <= var_group.status_code < 300:
        return var_group.json()
    else:
        print("No se pudieron obtener las variables para el ID de Grupo {}".format(project_group_id))


# Borro la variable en base a un tag

def delete_group_variables(group_id, key_variable):
    endpoint = "{}{}/groups/{}/variables/{}".format(GITLAB_URL, GITLAB_API, group_id, key_variable)

    var_group = requests.delete(endpoint,
                                verify=False,
                                headers=HEADER
                                )
    if 200 <= var_group.status_code < 300:
        print("Se borro con exito la variable {} del grupo ID {}".format(key_variable, group_id))
    else:
        print("No se pudo borrar la variable {} del grupo ID {}".format(key_variable, group_id))


# Configuro la variable de un grupo si no existe , en caso contrario la actualizo

def set_or_uodate_group_variables(project_group_id, var_name, create_json, actualizar):
    endpoint = "{}{}/groups/{}/variables/{}".format(GITLAB_URL, GITLAB_API, project_group_id, var_name)

    var_group = requests.get(endpoint,
                             verify=False,
                             headers=HEADER
                             )
    if 200 <= var_group.status_code < 300:
        if actualizar:
            hs_rules = requests.put(endpoint,
                                    verify=False,
                                    json=create_json,
                                    headers=HEADER
                                    )
            if 200 <= hs_rules.status_code < 300:
                print("Variable {} del Grupo ID {} Actualizada".format(var_name, project_group_id))
            else:
                print("No se pudo actualizar {} la Variable del Grupo ID {}".format(var_name, project_group_id))
        print("No se pidio actualizar {} la Variable del Grupo ID {}".format(var_name, project_group_id))
    else:
        endpoint = "{}{}/groups/{}/variables".format(GITLAB_URL, GITLAB_API, project_group_id)

        hs_rules = requests.post(endpoint,
                                 verify=False,
                                 json=create_json,
                                 headers=HEADER
                                 )
        if 200 <= hs_rules.status_code < 300:
            print("Variable {} del Grupo ID {} Creada".format(var_name, project_group_id))
        else:
            print("No se pudo crear la Variable {}  del Grupo ID {}".format(var_name, project_group_id))


# Setea variables en repositorio

def set_variable_python_gitlab(svpgproject_id, variables_project_dict):
    project = gl.projects.get(svpgproject_id)
    json_loads = json.loads(variables_project_dict)
    status = ''
    svpg_msg = ''
    variable = ''
    variables_status_list = {}
    for k, v in json_loads.items():
        try:
            variable = project.variables.get(k)
            svpg_msg = f"Variable {k} ya existe"
            status = ''
        except ValueError:
            print(f"Variable {k} no existe")

        if variable == '':
            try:
                print(f"###DevOps Message: seteando variable {k}")
                var = project.variables.create({'key': f"{k}", 'value': f"{v}"})

                if var.key:
                    svpg_msg = f"variable {var.key} creada"
                    status = 'ok'

            except RuntimeError:
                svpg_msg = f"No se pudo crear la variable {k}"
                status = 'not ok'

        print("{} {}".format(status, svpg_msg))
        variables_status_list[k] = status
    print(variables_status_list)
    return variables_status_list


def get_projects_by_topic(topic_key, topic_value):
    """
    topic_endpoint = "{}{}/projects?topic={}:{}&per_page=500&sort=asc".format(GITLAB_URL, GITLAB_API, topic_key,
                                                        topic_value)
    """
    page_init = 1
    endpoint = "{}{}/projects?topic={}:{}&per_page=100&sort=asc&page={}&archived=false".format(
        GITLAB_URL,
        GITLAB_API,
        topic_key,
        topic_value,
        page_init)
    project_list = []

    response = requests.get(endpoint, verify=False, headers=HEADER)

    if 200 <= response.status_code < 300:
        project_list_json = response.json()
        total_page = int(response.headers["X-Total-Pages"])
        total_page = total_page + page_init
        for page in range(2, total_page):
            endpoint = "{}{}/projects?topic={}:{}&per_page=100&sort=asc&page={}&archived=false".format(
                GITLAB_URL,
                GITLAB_API,
                topic_key,
                topic_value,
                page)

            response = requests.get(endpoint, verify=False, headers=HEADER)
            if 200 <= response.status_code < 300:
                project_list_json2 = response.json()
                project_list_json += project_list_json2

        for project in project_list_json:
            print("Agregando proyecto {}".format(project["id"]))
            project_id_by_topic = str(project["id"])
            project_list.append(project_id_by_topic)

    return project_list


def get_cmdbs_name_list(all_cmdbs_applications):
    if all_cmdbs_applications:
        cmdb_name_list = []
        '''print(all_cmdbs_applications)'''
        for cmdb_application in all_cmdbs_applications:
            cmdb_name = cmdb_application['name']
            cmdb_name_list.append(cmdb_name)

        cmdb_name_list.sort()
        print(cmdb_name_list)
        return cmdb_name_list
    else:
        print("cmdb list vacia")


def get_project_ids_list(cmdb_list):
    # aca habria que agregar un diccionario de cmdbs con sus listas de repos ids
    cmdb_id_repos = {}
    '''project_ids_list = []'''
    for cmdb in cmdb_list:
        print(f"Recuperando id de proyectos para cmdb {cmdb}")
        project_ids_list_by_topic = get_projects_by_topic('CMDB', cmdb)
        if project_ids_list_by_topic:
            cmdb_id_repos[cmdb] = project_ids_list_by_topic
        '''project_ids_list.append(project_ids_list_by_topic)'''
    '''project_ids_list = itertools.chain(*project_ids_list)
    project_ids_list = list(project_ids_list)'''
    return cmdb_id_repos


def generate_project_id_list():
    all_cmdbs_applications = get_cmdbs()
    cmdb_name_list = get_cmdbs_name_list(all_cmdbs_applications)
    repositories_id_by_cmdb_list = get_repositories_by_cmdb_list(cmdb_name_list)

    return repositories_id_by_cmdb_list


def get_repositories_by_cmdb_list(cmdb_name_list):
    project_id_list_by_cmdb_dict = {}
    if cmdb_name_list:
        project_id_list_by_cmdb_dict = get_project_ids_list(cmdb_name_list)
    else:
        print("Lista vacia de nombres de cmdbs")
    return project_id_list_by_cmdb_dict


def get_cmdb_topic_from_project(gctf_project_gitlab):
    topics = gctf_project_gitlab['topics']
    cmdb_project = topics[0]
    cmdb_subc = 'sin cmdb'
    if 'CMDB' in cmdb_project:
        indice_c = cmdb_project.index(':')  # obtenemos la posición del carácter c
        indice_init = indice_c + 1
        indice_final = len(cmdb_project)
        print(cmdb_project)
        print(indice_init)
        print(indice_final)
        cmdb_subc = cmdb_project[indice_init:indice_final]
        print(cmdb_subc)
    return cmdb_subc


def get_file_branch(gfb_project_id, gfb_file_name, gfb_branch_name):
    ptd_branch_endpoint = '{}{}/projects/{}/repository/files/{}?ref={}'. \
        format(GITLAB_URL, GITLAB_API, gfb_project_id, gfb_file_name, gfb_branch_name)

    response = requests.get(ptd_branch_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la info del archivo")


def unset_topic_to_project(unst_project_id, tag_list, topic_to_remove):
    # msg = ''
    # status = ''
    topic_status_list = {}
    if topic_to_remove in tag_list:
        print(topic_to_remove)
        tag_list.remove(topic_to_remove)
        print(tag_list)
        topics_json = {
            'tag_list': tag_list
        }
        resp = put_project(topics_json, unst_project_id)
        if resp != '':
            if not 200 <= resp.status_code < 300:
                unst_msg = "No se pudo eliminar el topic del proyecto por {}".format(resp.text)
                status = 'no eliminado'
            else:
                unst_msg = "Topic {} eliminado del proyecto {} ".format(topic_to_remove, unst_project_id)
                status = 'eliminado'

        else:
            unst_msg = "No se pudo pushear la eliminacion del topic en el proyecto"
            status = 'algo paso'
    else:
        unst_msg = "Tag no se encuentra en topics"
        status = 'no existe'

    print(unst_msg)
    topic_status_list[topic_to_remove] = status
    return topic_status_list


def containGitlab_ci(cgCI_project_id):
    allow_merge = False
    response_json = get_file_branch(cgCI_project_id, ".gitlab-ci.yml", "development")
    if response_json is not None:
        allow_merge = True
    print("Contiene gitlab-ci {}".format(allow_merge))
    return allow_merge


def get_user_id(gitlab_user):
    """ In Parameter: A bank user id (AXXXXXXX)
        Out Parameter: A json with the users gitlab API
        Function: Gets user information from gitlab API based on bank UID
    """
    response = ''
    if re.match('^[A-B][0-9]{6}$', gitlab_user.lstrip('@').upper()):
        response = requests.get('{}{}/users?extern_uid=cn={},ou=users,'
                                'ou=usuarios,ou=central,dc=rio,dc=ar,dc=bsch&provider=ldapmain'
                                .format(GITLAB_URL, GITLAB_API,
                                        gitlab_user.lstrip('@')),
                                headers=HEADER,
                                verify=False)

    if response.json():

        return response.json()[0]
    else:
        print("No se pudieron obtener los head/sponsors para el gitlab_user: {}".format(gitlab_user))


# Obtengo todas las integraciones que tiene el proyecto

def get_integration(gInt_project_id):
    ptd_branch_endpoint = '{}{}/projects/{}/services'. \
        format(GITLAB_URL, GITLAB_API, gInt_project_id)

    response = requests.get(ptd_branch_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudieron obtener las integraciones")


# Obtengo la información de Container Registry

def get_registry(getReg_project_id):
    ptd_branch_endpoint = '{}{}/projects/{}/registry/repositories'. \
        format(GITLAB_URL, GITLAB_API, getReg_project_id)

    response = requests.get(ptd_branch_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la info de la registry")


def block_user(user_id):
    """ In Parameter: A Gitlab User ID (number)
        Out Parameter: A json response if its blocked correctly
        Function: Blocks a user by id
    """
    ptd_branch_endpoint = '{}{}/users/{}/block'. \
        format(GITLAB_URL, GITLAB_API, user_id)
    response = requests.get(ptd_branch_endpoint, verify=False)
    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo bloquear el usuario id: {}".format(user_id))


def unblock_user(user_id):
    """ In Parameter: A Gitlab User ID (number)
        Out Parameter: A json response if its unblocked correctly
        Function: Unblocks a user by id
    """
    ptd_branch_endpoint = '{}{}/users/{}/unblock'. \
        format(GITLAB_URL, GITLAB_API, user_id)
    response = requests.get(ptd_branch_endpoint, verify=False)
    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo desbloquear el usuario id: {}".format(user_id))


def get_sponsors_to_block():
    """ In Parameter: None
        Out Parameter: A list of Gitlab User API information
        Function: Returns a list of sponsors that should be blocked from gitlab.ar.bsch
        based on the sponsors loaded on https://applications-api-devops.apps.ocpprd.ar.bsch/api/v1.0/programs
    """
    programas = get_app_programas()
    programName = {}
    sponsors = []
    for programa in programas['data']:
        programName[programa['id']] = programa['name']

    for gstb_id, name in programName.items():
        integrantes = get_app_head(gstb_id)
        memberlist = integrantes['memberships']
        for member in memberlist:
            if (member['role'] == "SPONSORS") or (member['role'] == "SPONSOR_TEMP_APPROVAL"):
                sponsors.append(member['username'])
    # remove duplicate sponsors
    sponsors = list(set(sponsors))
    sponsors_a_bloquear = []
    for sponsor in sponsors:
        sponsor_data = get_user_id(sponsor)
        if sponsor_data is not None:
            if sponsor_data['email'].endswith("@santander.com.ar") or sponsor_data['email'].endswith(
                    "@santanderrio.com.ar"):
                if sponsor_data['state'] == "active":
                    sponsors_a_bloquear.append(sponsor_data)

    return sponsors_a_bloquear


def get_value_by_key_inside_a_list(list_to_get_value_from, key):
    """ In Parameter: A list with a dictionary inside, and a key to serach for
        Out Parameter: A list with with only the values from the key in the dictionary
        Function: Returns a list of values based ona a key inside the dictionary.
        e.g : songs = [
            {"title": "Cuando caiga la noche", "playcount": 4},
            {"title": "Si Usted la viera", "playcount": 2},
            {"title": "Wonderwall", "playcount": 6}
            ]
        get_value_by_key_inside_a_list(songs,"title")
        returns: ["Cuando caiga la noche","Si Usted la viera","Wonderwall"]
    """
    # Si en algun momento se quiere usar list comprehension
    # return [x[key] for x in list_to_get_value_from]
    return list(map(lambda x: x[key], list_to_get_value_from))


def delete_variable_python_gitlab(project_id, variable_key):
    project = gl.projects.get(project_id)
    status = ''
    dvpg_msg = ''
    variables_status_list = {}
    if project is not None:
        try:
            variable = project.variables.get(variable_key)
            if variable != '':
                project.variables.delete(variable_key)
                variable = project.variables.get(variable_key)
                if variable != '':
                    dvpg_msg = f"variable {variable_key} sigue existiendo, algo paso"
                    status = 'sigue existiendo'
            else:
                dvpg_msg = f"variable {variable_key} no existe"
        except ValueError:
            dvpg_msg = f"variable {variable_key} no existe"
            status = "no existe"
    print(dvpg_msg)
    variables_status_list[variable_key] = status
    return variables_status_list


def block_all_sponsors():
    sponsor_to_block = get_sponsors_to_block()
    id_sponsor = get_value_by_key_inside_a_list(sponsor_to_block, 'id')

    for bas_id in id_sponsor:
        block_user(bas_id)


# Obtengo la información de los tags dentro del Container Registry

def get_all_registry_tags(getAllReg_project_id, registry_id):
    ptd_branch_endpoint = '{}{}/projects/{}/registry/repositories/{}/tags'. \
        format(GITLAB_URL, GITLAB_API, getAllReg_project_id, registry_id)

    response = requests.get(ptd_branch_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la info de los tags")


# Obtengo la información del tag dentro del Container Registry

def get_registry_tags(getRegTags_project_id, registry_id, tag_name):
    ptd_branch_endpoint = '{}{}/projects/{}/registry/repositories/{}/tags/{}'. \
        format(GITLAB_URL, GITLAB_API, getRegTags_project_id, registry_id, tag_name)

    response = requests.get(ptd_branch_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la info del tag")


# Obtengo todos los ambientes del proyecto

def get_environments(getEnv_project_id):
    ptd_branch_endpoint = '{}{}/projects/{}/environments'. \
        format(GITLAB_URL, GITLAB_API, getEnv_project_id)

    response = requests.get(ptd_branch_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la info de los ambientes")


# Obtengo la información del ambiente

def get_environment_info(getEnvin_project_id, environement_id):
    ptd_branch_endpoint = '{}{}/projects/{}/environments/{}'. \
        format(GITLAB_URL, GITLAB_API, getEnvin_project_id, environement_id)

    response = requests.get(ptd_branch_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la info del ambiente solicitado")


# Obtengo un proyecto por el nombre completo

def get_project_by_name(project_name):
    ptd_branch_endpoint = '{}{}/projects?search="{}"'. \
        format(GITLAB_URL, GITLAB_API, project_name)

    response = requests.get(ptd_branch_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        project = response.json()
        if project:
            return project[0]
        else:
            print("No existe el proyecto")
            return []
    else:
        print("No se pudo obtener la info del proyecto buscado")


# Obtengo el listado de Runners de Gitlab

def get_all_runners():
    page_init = 1
    endpoint = "{}{}/runners/all?&per_page=100&sort=asc&page={}&archived=false".format(
        GITLAB_URL,
        GITLAB_API,
        page_init)
    runners_list = []

    response = requests.get(endpoint, verify=False, headers=HEADER)

    if 200 <= response.status_code < 300:
        runners_list = response.json()
        total_page = int(response.headers["X-Total-Pages"])
        total_page = total_page + page_init
        for page in range(2, total_page):
            endpoint = "{}{}/runners/all?&per_page=100&sort=asc&page={}&archived=false".format(
                GITLAB_URL, GITLAB_API, page)

            response = requests.get(endpoint, verify=False, headers=HEADER)
            if 200 <= response.status_code < 300:
                runners_list_json2 = response.json()
                runners_list += runners_list_json2
    return runners_list


# Obtengo la información de un Runner Especifico

def get_runner_data(runner_id):
    ptd_branch_endpoint = '{}{}/runners/{}'. \
        format(GITLAB_URL, GITLAB_API, runner_id)

    response = requests.get(ptd_branch_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la información del Runner Solicitado")


# Obtengo todos los runners con un tag Especifico


def get_all_runners_by_tag(tag_list):
    page_init = 1
    endpoint = "{}{}/runners/all?tag_list={}&per_page=100&sort=asc&page={}&archived=false".format(
        GITLAB_URL,
        GITLAB_API,
        tag_list,
        page_init)
    runners_list = []

    response = requests.get(endpoint, verify=False, headers=HEADER)

    if 200 <= response.status_code < 300:
        runners_list = response.json()
        total_page = int(response.headers["X-Total-Pages"])
        if total_page > 1:
            total_page = total_page + page_init
            for page in range(2, total_page):
                endpoint = "{}{}/runners/all?tag_list={}&per_page=100&sort=asc&page={}&archived=false".format(
                    GITLAB_URL, GITLAB_API, tag_list, page)

                response = requests.get(endpoint, verify=False, headers=HEADER)
                if 200 <= response.status_code < 300:
                    runners_list_json2 = response.json()
                    runners_list += runners_list_json2
    return runners_list


# Borra un Runner

def delete_runner(runner_id):
    endpoint = '{}{}/runners/{}' \
        .format(GITLAB_URL, GITLAB_API, runner_id)

    update = requests.delete(endpoint,
                             verify=False,
                             headers=HEADER
                             )
    if 200 <= update.status_code < 300:
        print("Se pudo borrar el Runner ID {}".format(runner_id))
    else:
        print("No se pudo borrar el Runner ID {}".format(runner_id))


# Creo un Merge Request

def create_merge_request(cmr_project_id, mr_sb, mr_tg, mr_title, mr_desp, mr_squash):
    mr_endpoint = '{}{}/projects/{}/merge_requests'. \
        format(GITLAB_URL, GITLAB_API, cmr_project_id)

    mr_json = {
        "source_branch": mr_sb,
        "target_branch": mr_tg,
        "title": mr_title,
        'merge_when_pipeline_succeeds': True,
        "description": mr_desp,
        "squash": mr_squash
    }

    mr_post = requests.post(mr_endpoint,
                            headers=HEADER,
                            json=mr_json,
                            verify=False)

    if 200 <= mr_post.status_code < 300:
        print("Merge Request Created")
        return mr_post.json()
    else:
        print("No se pudo crear el MR Solicitado por Código de Error: {}".format(mr_post.status_code))


# Verifico la información de un MR

def merge_request_info(mri_project_id, mr_iid):
    mr_info_endpoint = '{}{}/projects/{}/merge_requests/{}'. \
        format(GITLAB_URL, GITLAB_API, mri_project_id, mr_iid)

    response = requests.get(mr_info_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la información del MR Solicitado")


# Obtengo la información de una Pipeline

def pipeline_info(pipe_project_id, pipeline_id):
    pipe_info_endpoint = '{}{}/projects/{}/merge_requests/{}'. \
        format(GITLAB_URL, GITLAB_API, pipe_project_id, pipeline_id)

    response = requests.get(pipe_info_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la información del Pipeline Solicitado")


# Obtengo la información de los jobs de una Pipeline

def pipeline_jobs_info(pipeji_project_id, pipeline_id):
    pipe_info_endpoint = '{}{}/projects/{}/merge_requests/{}/jobs'. \
        format(GITLAB_URL, GITLAB_API, pipeji_project_id, pipeline_id)

    response = requests.get(pipe_info_endpoint,
                            headers=HEADER,
                            verify=False)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        print("No se pudo obtener la información del Pipeline Solicitado")


# Confirmo el MR solicitado previamente


def accept_merge_request(amr_project_id, mr_iid):
    merge = False
    mr_info = merge_request_info(amr_project_id, mr_iid)
    if not mr_info["has_conflicts"]:
        if int(mr_info["changes_count"]) > 0:
            print("Verificando estado del Pipeline del MR")
            time.sleep(60)
            mr_info = merge_request_info(amr_project_id, mr_iid)
            pipe_st = mr_info["pipeline"]["status"]
            while pipe_st == "running":
                print("Verificando estado del Pipeline del MR")
                time.sleep(30)
                mr_info = merge_request_info(amr_project_id, mr_iid)
                pipe_st = mr_info["pipeline"]["status"]
            if pipe_st == "success":
                merge = True
            else:
                print("El Pipeline del MR Fallo")
        else:
            print("Su MR no tiene cambios")
    else:
        print("Su MR Tiene Conflcitos")

    if merge:
        mr_endpoint = '{}{}//projects/{}/merge_requests/{}/merge'. \
            format(GITLAB_URL, GITLAB_API, amr_project_id, mr_iid)

        mr_post = requests.put(mr_endpoint,
                               headers=HEADER,
                               verify=False)

        if 200 <= mr_post.status_code < 300:
            return mr_post.json()
        else:
            print("No se pudo Aceptar el MR Solicitado")


# Obtengo la información de los tags generado desde una branch

def get_tag(gtt_project_id, tag_name):
    gtt_endpoint = '{}{}/projects/{}/repository/tags/{}'. \
        format(GITLAB_URL, GITLAB_API, gtt_project_id, tag_name)
    return generenic_get(gtt_endpoint, "Tag {}".format(tag_name))

# Borro un tag generado desde una branch

def delete_tag(gtt_project_id, tag_name):
    gtt_endpoint = '{}{}/projects/{}/repository/tags/{}'. \
        format(GITLAB_URL, GITLAB_API, gtt_project_id, tag_name)
    return generic_delete(gtt_endpoint, "Tag {}".format(tag_name))


# Protejo un tag generado desde una branch

def protected_tag(gtt_project_id, tag_name):
    gtt_endpoint = '{}{}/projects/{}/protected_tags'. \
        format(GITLAB_URL, GITLAB_API, gtt_project_id)
    protected_tag_json = {
        "name": tag_name,
        "create_access_level": 30
    }
    return generenic_post(gtt_endpoint, protected_tag_json, "Protec Tag {}".format(tag_name))


def get_pipelines(gtp_project_id):
    gtt_endpoint = '{}{}/projects/{}/pipelines?ref=main'. \
        format(GITLAB_URL, GITLAB_API, gtp_project_id)
    return generenic_pag_get(gtt_endpoint, "Pipeline")


def get_project_template(project_id, branch_name):
    fci = get_file_branch(project_id, '.gitlab-ci.yml', branch_name)
    if fci is not None:
        ci_file = base64.b64decode(fci['content']).decode('utf-8')
        for line in ci_file.splitlines():
            linea = re.sub('[\"\' ]', '', line)
            if not linea.strip().startswith('#'):
                if "file:" in linea:
                    return linea.split(":")[1]
