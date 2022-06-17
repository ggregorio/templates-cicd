from datetime import datetime, timedelta

import urllib3
from termcolor import colored

from sta_gitlab import get_project_template
from quay import *

urllib3.disable_warnings()
# today = datetime.utcnow().strftime("%d") + ' ' + datetime.utcnow().strftime("%B")[0:3] + ',' + datetime.utcnow(
# ).strftime("%Y")
JOB_ID = sys.argv[1]
JOB_DATE = sys.argv[2][0:10] + ' ' + sys.argv[2][11:19]
BRANCH = sys.argv[3]
PATH = sys.argv[4]

p_type = get_project_template(JOB_ID, BRANCH)
dockerTemplate = False
if p_type:
    if 'dockerImage' in p_type:
        dockerTemplate = True
    job_date = datetime.strptime(JOB_DATE, '%Y-%m-%d %H:%M:%S') + timedelta(hours=3) - timedelta(minutes=5)
    all_images = get_images(JOB_ID, dockerTemplate, PATH)
    tags = get_images_tags(JOB_ID, dockerTemplate, PATH)
    print(colored("Comenzando a trabajar con el proyecto {}".format(JOB_ID), 'magenta'))
    print(colored("Buscando el tag con el nombre {}".format(BRANCH), 'blue'))
    hora_anterior = job_date
    ultimo_tag = ''
    ultima_actualizacion = ''
    if tags["tags"]:
        for tag in tags["tags"]:
            ultima_actualizacion = str(tag["last_modified"][5:-20]) + ',' + str(tag["last_modified"][12:-6])
            hora = datetime.strptime(ultima_actualizacion, '%d %b,%Y %H:%M:%S')
            if hora >= job_date and tag["name"] == BRANCH:
                if hora > hora_anterior:
                    hora_anterior = hora
                    ultimo_tag = dict(tag)
        if ultimo_tag:
            hora_anterior = hora_anterior - timedelta(hours=3)
            print(colored("La imagen se encuentra en Quay y se genero a las {}".format(hora_anterior), 'green'))
            vulnerabilites = get_image_vulnerabilities(JOB_ID, dockerTemplate, PATH, ultimo_tag["manifest_digest"])
            date = datetime.today()
            max_time = date + timedelta(minutes=2)
            if vulnerabilites == 2:
                print(colored("Quay nos informa que no se puede realizar el analisis de vulnerabilidades de la  imagen",
                              'red'))
                exit(1)
            if vulnerabilites == 1:
                print(colored("Quay nos informa que el analisis de vulnerabilidades de la  imagen esta pendiente",
                              'red'))
                print(colored("Reintentando Durante 2 Minutos", 'red'))
            notScanned = False
            while vulnerabilites == 1 or date < max_time:
                vulnerabilites = get_image_vulnerabilities(JOB_ID, dockerTemplate, PATH, ultimo_tag["manifest_digest"])
                if vulnerabilites != 1:
                    notScanned = False
                    break
                date = datetime.today()
                notScanned = True
            if notScanned:
                if dockerTemplate:
                    print(colored("Verificar cuando este concluido en "

                                  "https://{}/repository/santandertec/{}?tab=tags "
                                  "y volver a ejecutar".format(QUAY_URL, PATH),
                                  'red'))
                else:
                    print(colored("Verificar cuando este concluido en "
                                  "https://{}/repository/santandertec/gitlab-projectid-{}?tab=tags "
                                  "y volver a ejecutar".format(QUAY_URL, JOB_ID),
                                  'red'))
                exit(1)
            else:
                print(colored("Verificando si la imagen tiene vulnerabilidades", 'blue'))
                if vulnerabilites:
                    vulnerabilites_data = vulnerabilites["data"]["Layer"]["Features"]
                    positive = False
                    for vulnerability in vulnerabilites_data:
                        if vulnerability["Vulnerabilities"]:
                            print(colored("La vulnerabilidad {} existe", 'cyan').format(vulnerability["Name"]))
                            for vulne in vulnerability['Vulnerabilities']:
                                print(colored("Se detecto {}, Info {}, Fixed {}, Severity {}", 'yellow').format(
                                    vulne["Name"], vulne["Link"], vulne["FixedBy"], vulne["Severity"]))
                            positive = True

                    if not positive:
                        print(colored("No se encontraron", 'green'))
                        exit(0)
                    else:
                        exit(1)
        else:
            print(colored("No se encontro la imagen con el Tag {}".format(BRANCH), 'red'))
            exit(1)
    else:
        print(colored("No se tiene ningun TAG", 'red'))
        exit(1)
else:
    print(colored(".gitlab-ci.yml perteneciente a la rama {}".format(BRANCH), 'red'))
    exit(1)
