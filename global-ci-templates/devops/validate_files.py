import ast
from datetime import datetime, timedelta

import urllib3
from termcolor import colored

from quay import *

urllib3.disable_warnings()
# today = datetime.utcnow().strftime("%d") + ' ' + datetime.utcnow().strftime("%B")[0:3] + ',' + datetime.utcnow(
# ).strftime("%Y")
JOB_ID = sys.argv[1]
JOB_DATE = sys.argv[2][0:10] + ' ' + sys.argv[2][11:19]
BRANCH = sys.argv[3]
FRONT = ''
if sys.argv[4] == 'true' or sys.argv[4] == 'True':
    FRONT = True
elif sys.argv[4] == 'false' or sys.argv[4] == 'False':
    FRONT = False
environment = ''
if 'dev' in BRANCH:
    environment = 'development'
elif 'develop-maintenance' in BRANCH:
    environment = 'dev-maintenance'
elif 'staging' in BRANCH:
    environment = 'staging'
elif 'master' in BRANCH and FRONT:
    environment = 'production'
elif 'master' in BRANCH:
    environment = 'stable'

job_date = datetime.strptime(JOB_DATE, '%Y-%m-%d %H:%M:%S') + timedelta(hours=3) - timedelta(minutes=5)
# all_images = get_images(JOB_ID)
tags = get_images_tags(JOB_ID)
print(colored("Comenzando a trabajar con el proyecto {}".format(JOB_ID), 'magenta'))
for tag in tags["tags"]:
    ultima_actualizacion = str(tag["last_modified"][5:-20]) + ',' + str(tag["last_modified"][12:-6])
    hora = datetime.strptime(ultima_actualizacion, '%d %b,%Y %H:%M:%S')
    print(colored("Buscando el tag con el nombre {}".format(environment), 'blue'))
    if hora >= job_date and tag["name"] == environment:
        # manifest = get_manifest("6587", tag["manifest_digest"])
        # print(colored(manifest, 'yellow'))
        print(colored("La imagen se encuentra en Quay", 'green'))
        vulnerabilites = get_image_vulnerabilities("6587", tag["manifest_digest"])
        print(colored("Verificando si la imagen tiene vulnerabilidades", 'blue'))
        positive = False
        for vulnerability in vulnerabilites["data"]["Layer"]["Features"]:
            if vulnerability["Vulnerabilities"]:
                print(colored("La vulnerabilidad {} fue detectada", 'yellow'))
                positive = True
        if not positive:
            print(colored("No se encontraron".format(tag["name"]), 'green'))
            exit(0)
    else:
        print(colored("No se encontro la imagen del ambiente {}".format(environment), 'red'))
        exit(1)
