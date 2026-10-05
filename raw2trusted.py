import io
import pandas as pd
import numpy as np
from config_aws import *
from captura import upload_file
import shutil 

def listar_chaves(prefixo):
    paginator = s3_client.get_paginator('list_objects_v2')
    params = {
        'Bucket': os.getenv('BUCKET_NAME'),
        'Prefix': prefixo
    }

    page_iterator = paginator.paginate(**params)
    chaves = []

    for pagina in page_iterator:
        for obj in pagina.get('Contents', []):
            chave = obj['Key']

            if chave.endswith('.csv'):
                chaves.append(chave)
    
    return chaves

def transformar_chave(chave_raw):
    if chave_raw.startswith('raw/'):
            nova_chave = chave_raw.replace('raw/', 'trusted/', 1)
    else:
        raise ValueError(f'Chave não começa com raw/: {chave_raw}')

    return nova_chave

def listar_pendentes():
    chaves = {
        'chaves_raw': set(listar_chaves('raw/')),
        'chaves_trusted': set(listar_chaves('trusted/'))
    }

    pendentes = []

    for chave_raw in chaves['chaves_raw']:
        chave_transformada = transformar_chave(chave_raw)

        if chave_transformada not in chaves['chaves_trusted']:
           pendentes.append(chave_raw)

    return sorted(pendentes)

def baixar_arquivo(chave_raw):
    caminho_local = 'raw_local/' + chave_raw
    diretorio = os.path.dirname(caminho_local)

    os.makedirs(diretorio, exist_ok=True)

    s3_client.download_file(os.getenv('BUCKET_NAME'), chave_raw, caminho_local)

    return caminho_local

def ler_csv(caminho):
    df = pd.read_csv(caminho, sep=';')

    return df

def limpar(df):
    colunas_numericas = [
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

    colunas_sem_negativos = [
    'CPU_FREQ_ATUAL',
    'CPU_COUNT_LOGICA',
    'LOAD_AVG_1',
    'LOAD_AVG_5',
    'LOAD_AVG_15',
    ]

    colunas_percentual = [
    'CPU_PERCENT',
    'CPU_USER_PERCENT',
    'CPU_SYSTEM_PERCENT',
    'CPU_IDLE_PERCENT',
    'CPU_IOWAIT_PERCENT',
    'RAM_PERCENT',
    'SWAP_PERCENT',
    'DISCO_PERCENT'
    ]

    colunas_bytes = [
    'RAM_TOTAL',
    'RAM_AVAILABLE',
    'RAM_USED',
    'SWAP_USED',
    'SWAP_FREE',
    'SWAP_IN',
    'SWAP_OUT',
    'DISCO_TOTAL',
    'DISCO_USED',
    'DISCO_FREE'
    ]

    grupos_verificacao = {
        'CPU': ['CPU_PERCENT', 'CPU_USER_PERCENT', 'CPU_SYSTEM_PERCENT', 'CPU_IDLE_PERCENT', 'CPU_IOWAIT_PERCENT', 'CPU_FREQ_ATUAL', 'CPU_COUNT_LOGICA', 'LOAD_AVG_1', 'LOAD_AVG_5', 'LOAD_AVG_15'],
        'RAM': ['RAM_PERCENT','RAM_TOTAL','RAM_AVAILABLE','RAM_USED'],
        'SWAP': ['SWAP_PERCENT','SWAP_USED','SWAP_FREE','SWAP_IN','SWAP_OUT'],
        'DISCO': ['DISCO_PERCENT','DISCO_TOTAL','DISCO_USED','DISCO_FREE']
    }

    df = df.copy()

    df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'], errors='coerce')

    for coluna in colunas_numericas:
        df[coluna] = pd.to_numeric(df[coluna], errors='coerce').astype('float64')

    for coluna in colunas_percentual:
        invalido = (df[coluna] < 0) | (df[coluna] > 100)
        df.loc[invalido, coluna] = np.nan

    for coluna in colunas_bytes:
        invalido = df[coluna] < 0
        df.loc[invalido, coluna] = np.nan

    for coluna in colunas_sem_negativos:
        invalido = df[coluna] < 0
        df.loc[invalido, coluna] = np.nan

    for grupo, lista in grupos_verificacao.items():
        nao_monitorado = (df[lista] == 0).all(axis=1)
        df.loc[nao_monitorado, lista] = np.nan
 
    df = df.dropna(subset=colunas_numericas, how='all')
    df.dropna(subset=['TIMESTAMP'], inplace=True)
    df.drop_duplicates(
        subset=['HOSTNAME', 'TIMESTAMP'],
        keep='first',
        inplace=True
    )

    df['CPU_COUNT_LOGICA'] = df['CPU_COUNT_LOGICA'].astype('Int64')
    for coluna in colunas_bytes:
        df[coluna] = df[coluna].astype('Int64')

    return df

def gravar_csv(df, chave_raw):
    caminho_saida = 'trusted_local/' + transformar_chave(chave_raw)
    diretorio = os.path.dirname(caminho_saida)

    os.makedirs(diretorio, exist_ok=True)

    df.to_csv(caminho_saida, sep=';', index=False, date_format='%Y-%m-%d %H:%M:%S', na_rep='')

    return caminho_saida


def processar(chave_raw):
    caminho = baixar_arquivo(chave_raw)

    df_lido = ler_csv(caminho)
    df_limpo = limpar(df_lido)

    file_trusted = gravar_csv(df_limpo, chave_raw)
    chave_destino = transformar_chave(chave_raw)

    return upload_file(file_trusted, os.getenv('BUCKET_NAME'), chave_destino)

if __name__ == '__main__':
    try:
        chaves_pendentes = listar_pendentes()

        for chave_atual in chaves_pendentes:
            processar(chave_atual)

        print('ETL concluída! :)')

    finally:
        shutil.rmtree('raw_local', ignore_errors=True)
        shutil.rmtree('trusted_local', ignore_errors=True)

        print('Arquivos locais temporários removidos!')


    print(listar_chaves('trusted/'))
    