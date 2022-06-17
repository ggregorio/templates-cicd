import sys
import requests
import re
from termcolor import colored

URL_TOKEN = "https://accounts.google.com/o/oauth2/token"
URL_UPLOAD_BASE = "https://www.googleapis.com/upload/chromewebstore/v1.1/items/"
URL_PUBLISH_BASE = "https://www.googleapis.com/chromewebstore/v1.1/items/"


def refresh_token(client_id, client_secret, refresh_token):
    payload = f'client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}&grant_type' \
              f'=refresh_token&redirect_uri=urn:ietf:wg:oauth:2.0:oob'.format(client_id=client_id,
                                                                              client_secret=client_secret,
                                                                              refresh_token=refresh_token)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", URL_TOKEN, headers=headers, data=payload, verify=False)
    if response.status_code != 200:
        raise ValueError(colored("NO SE PUDO EXTREAR EL TOKEN: %s" % (str(response)), "red"))
    else:
        print(colored("TOKEN OBTENIDO CORRECTAMENTE : %s" % (str(response)), "blue"))
        json_resp = eval(response.content)
        return json_resp["access_token"]


def publish(application_id, token_in):
    url = URL_PUBLISH_BASE + application_id + "/publish"

    payload = 'publishTarget=default'
    headers = {
        'Authorization': 'Bearer ' + token_in,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)

    if response.status_code != 200:
        raise ValueError(colored("NO SE PUDO PUBLICAR EL ARTEFACTO: %s" % (str(response)), "red"))
    else:
        print(colored("ARTEFACTO PUBLICADO : %s" % (str(response)), "blue"))
        return


def upload_artifact(application_id, file_path, token_in):
    url = URL_UPLOAD_BASE + application_id

    payload = {'uploadType': 'media'}
    splitter = file_path.split("/")
    zip_file = splitter[len(splitter) - 1]
    pattern = re.compile(".*\\.zip$")
    if re.match(pattern, zip_file):
        files = [
            ('file', (str(zip_file), open(file_path, 'rb'), 'application/zip'))
        ]
        headers = {
            'Authorization': 'Bearer ' + token_in
        }

        response = requests.request("PUT", url, headers=headers, data=payload, files=files, verify=False)
        if response.status_code != 200:
            raise ValueError(colored("NO SE PUDO SUBIR EL ARTEFACTO : %s" % (str(response)), "red"))
        else:
            publish(application_id, token_in)
    else:
        raise ValueError(colored("EL ARCHIVO NO ES VALIDO: POR FAVOR DEBE SER ZIP ", "red"))


if __name__ == '__main__':

    if len(sys.argv) == 6:
        CLIENT_ID = sys.argv[1]
        CLIENT_SECRET = sys.argv[2]
        REFRESH_TOKEN = sys.argv[3]
        FILE_PATH = sys.argv[4]
        APPLICATION_ID = sys.argv[5]
        print(colored("Extrayendo token", "green"))
        token = refresh_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
        upload_artifact(APPLICATION_ID, FILE_PATH, token)
    else:
        print(colored(
            "MENSAJE DE DEVOPS: DEBE LLAMAR AL SCRIPT CON CLIENT_ID CLIENT_SECRET REFRESH_TOKEN ARTIFAC_PATH "
            "APPLICATION_ID",
            "green"))
