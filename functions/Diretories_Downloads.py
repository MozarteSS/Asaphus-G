
# cria os diretórios do projeto
import os
def dir_project(project_name):
    path_ref = f"projects/{project_name}/ref"
    if not os.path.exists(path_ref):
        os.makedirs(path_ref)
    path_ = f"projects/{project_name}"
    return path_, path_ref


# download ref xrd
import requests
def cif_download(cod_id, dir_ref):
    url = f"http://www.crystallography.net/cod/{cod_id}.cif"
    response = requests.get(url)
    if response.status_code == 200:
        with open(f"{dir_ref}/cod_{cod_id}.cif", "wb") as f:
            f.write(response.content)
        print(f"Arquivo COD {cod_id} baixado com sucesso!")
    else:
        print("Erro ao baixar o arquivo.")