import logging
import os
import sys
import requests

GITLAB_PRIVATE_TOKEN = os.environ.get('GITLAB_TOKEN')

HEADER_GITLAB = {'PRIVATE-TOKEN': '{}'.format(GITLAB_PRIVATE_TOKEN)}

logging.basicConfig(level=logging.NOTSET)


def generenic_get(gg_endpoint, method_name):
    try:
        gg_response = requests.get(gg_endpoint,
                                   verify=False,
                                   headers=HEADER_GITLAB
                                   )
        if 200 <= gg_response.status_code < 300:
            return gg_response.json()
        else:
            print("No se pudo obtener la información de {} solicitada".format(method_name))
    except Exception:
        print(
            "###DevOps Message: Surgio inconveniente al obtener la información de {}"
            "por el siguiente motivo:".format(method_name))
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))


def generenic_pag_get(ggp_endpoint, method_name):
    try:
        page = 1
        list_all_project = []
        final_endpoint = '{}&per_page=100&page={}' \
                         '&sort=asc&archived=False'. \
            format(ggp_endpoint, page)

        gpg_responde = requests.get(final_endpoint,
                                    verify=False,
                                    headers=HEADER_GITLAB
                                    )
        if 200 <= gpg_responde.status_code < 300:
            paginas = int(gpg_responde.headers["X-Total-Pages"])
            list_all_project = gpg_responde.json()
            for page in range(0, paginas):
                final_endpoint = '{}&per_page=100&page={}' \
                                 '&sort=asc&archived=False'. \
                    format(ggp_endpoint, page + 1)
                page_projects = requests.get(final_endpoint,
                                             headers=HEADER_GITLAB,
                                             verify=False).json()
                list_all_project.extend(page_projects)
            return list_all_project
        else:
            print("No se pudo obtener la información de {} solicitada".format(method_name))
    except Exception:
        print(
            "###DevOps Message: Surgio inconveniente al obtener la información de {}"
            "por el siguiente motivo:".format(method_name))
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))


def generenic_post(gpo_endpoint, gpo_json, method_name):
    try:
        gpo_response = requests.post(gpo_endpoint,
                                     verify=False,
                                     json=gpo_json,
                                     headers=HEADER_GITLAB
                                     )
        if 200 <= gpo_response.status_code < 300:
            logging.info("POST {} realizado correctamente".format(method_name))
            return 200
        else:
            logging.error("No se pudo realizar el POST {} solicitado".format(method_name))
            return -1
    except Exception:
        print(
            "###DevOps Message: Surgio inconveniente al realizar el POST {}"
            "por el siguiente motivo:".format(method_name))
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))


def generenic_put(gpu_endpoint, gpu_json, method_name):
    try:
        gpu_response = requests.put(gpu_endpoint,
                                    verify=False,
                                    json=gpu_json,
                                    headers=HEADER_GITLAB
                                    )
        if 200 <= gpu_response.status_code < 300:
            print("PUT {} realizado correctamente".format(method_name))
            return 200
        else:
            print("No se pudo realizar el PUT {} solicitado".format(method_name))
            return -1
    except Exception:
        print(
            "###DevOps Message: Surgio inconveniente al realizar el PUT {}"
            "por el siguiente motivo:".format(method_name))
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))


def generic_delete(gd_endpoint, method_name):
    try:
        gpu_response = requests.delete(gd_endpoint,
                                       verify=False,
                                       headers=HEADER_GITLAB
                                       )
        if 200 <= gpu_response.status_code < 300:
            print("Delete {} realizado correctamente".format(method_name))
            return 200
        else:
            print("No se pudo realizar el Delete {} solicitado".format(method_name))
            return -1
    except Exception:
        print(
            "###DevOps Message: Surgio inconveniente al realizar el Delete {}"
            "por el siguiente motivo:".format(method_name))
        traceBack = sys.exc_info()
        typeError = traceBack[0]
        nameError = traceBack[1]
        tracebackError = traceBack[2].tb_frame
        print("{} {} {}".format(typeError, nameError, tracebackError))
