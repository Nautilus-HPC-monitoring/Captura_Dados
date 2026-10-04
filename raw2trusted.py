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

print(listar_chaves('raw/'))
