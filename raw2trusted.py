import io
import pandas as pd
from config_aws import *

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

