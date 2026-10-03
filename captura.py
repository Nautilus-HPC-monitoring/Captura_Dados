from config_aws import *
import requests
import psutil as p
import time
import csv
from datetime import datetime
import socket
import logging
from botocore.exceptions import ClientError

start_msg = '''
=========================================================================
                REALIZE SUA AUTENTICAÇÃO PARA PROSSEGUIR!
=========================================================================
'''

print(start_msg)

email = input('Email: ')
password = input('Senha: ')

host = socket.gethostname()
url_auth = "http://localhost:3000/api/autenticacao"

flags_monitoramento = {}
dados = []

def authComponentes(componentes):
    for componente in componentes:
        flags_monitoramento[componente['tipo']] = True

def coletar_cpu():
    if flags_monitoramento.get('CPU', False):
        cpu_times = p.cpu_times_percent()
        cpu_freq = p.cpu_freq()

        return [
            p.cpu_percent(),
            cpu_times.user,
            cpu_times.system,
            cpu_times.idle,
            cpu_times.iowait,
            cpu_freq.current,
            p.cpu_count(),
            p.getloadavg()[0],
            p.getloadavg()[1],
            p.getloadavg()[2]
        ]

    return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def coletar_ram():
    if flags_monitoramento.get('RAM', False):
        ram = p.virtual_memory()

        return [
            ram.percent,
            ram.total,
            ram.available,
            ram.used
        ]

    return [0, 0, 0, 0]


def coletar_swap():
    if flags_monitoramento.get('SWAP', False):
        swap = p.swap_memory()

        return [
            swap.percent,
            swap.used,
            swap.free,
            swap.sin,
            swap.sout
        ]

    return [0, 0, 0, 0, 0]


def coletar_disco():
    if flags_monitoramento.get('DISCO', False):
        disco = p.disk_usage('/')

        return [
            disco.percent,
            disco.total,
            disco.used,
            disco.free
        ]

    return [0, 0, 0, 0]

cabecalho = [
    'TIMESTAMP',
    'HOSTNAME',
    'USER',

    'CPU_PERCENT',
    'CPU_USER_PERCENT',
    'CPU_SYSTEM_PERCENT',
    'CPU_IDLE_PERCENT',
    'CPU_IOWAIT_PERCENT',
    'CPU_FREQ_ATUAL',
    'CPU_COUNT_LOGICA',
    'LOAD_AVG_1',
    'LOAD_AVG_5',
    'LOAD_AVG_15',

    'RAM_PERCENT',
    'RAM_TOTAL',
    'RAM_AVAILABLE',
    'RAM_USED',

    'SWAP_PERCENT',
    'SWAP_USED',
    'SWAP_FREE',
    'SWAP_IN',
    'SWAP_OUT',

    'DISCO_PERCENT',
    'DISCO_TOTAL',
    'DISCO_USED',
    'DISCO_FREE'
]
usuario = os.environ.get('USER')

def upload_file(file_name, bucket, object_name):
    if object_name is None:
        object_name.os.path.basename(file_name)

    try:
        response = s3_client.upload_file(file_name, bucket, object_name) 
    except ClientError as e:
        logging.error(e)
        return False
    
    return True


def escrita():
    with open('./data.csv', 'w', newline='') as csvfile:
        csv.writer(csvfile, delimiter=';').writerow(cabecalho)

    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cpu = coletar_cpu()
        ram = coletar_ram()
        swap = coletar_swap()
        disco = coletar_disco()

        linha = [
            timestamp,
            host,
            usuario,

            *cpu,
            *ram,
            *swap,
            *disco
        ]

        dados.append(linha)
        print(linha)

        with open('./data.csv', 'a', newline='') as csvfile:
            csv.writer(csvfile, delimiter=';').writerow(dados)

        if upload_file('./data.csv', os.getenv('BUCKET_NAME'), f'{os.getenv('FILE_KEY')}/data.csv'):
            print('Arquivo enviado com sucesso!')
        else: 
            print('Falha no envio')

        time.sleep(10)

try:
    res = requests.post(
        url_auth,
        json={
            "email": email,
            "senha": password,
            "hostname": host
        }
    )
    res.raise_for_status()

    res = res.json()
    print(res)

    if res.get("autenticado"):
        print("\nAutenticação realizada com sucesso!")
        print("Hostname:", res["mainframe"]["hostname"])

        componentes = res["componentes"]
        authComponentes(componentes)

        escrita()

    else:
        print("Falha na autenticação! Email e/ou senha incorretos")

except requests.exceptions.HTTPError as erro:
    print("Erro na autenticação:", erro)

except requests.exceptions.RequestException as erro:
    print("Não foi possível conectar à API:", erro)

