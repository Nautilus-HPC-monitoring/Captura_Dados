import csv
import utils.exibicao as ex
import utils.cpu.cpu as cpu

cabecalho = [
    'TIMESTAMP',
    'USUARIO',

    'CPU_PERCENT',
    'CPU_USER_PERCENT',
    'CPU_SYSTEM_PERCENT',
    'CPU_IDLE_PERCENT',
    'CPU_IOWAIT_PERCENT',

    'CPU_INTERRUPTS',
    
    'CPU_FREQ_ATUAL',

    'LOAD_AVG_1',
    'LOAD_AVG_5',
    'LOAD_AVG_15',

    'RAM_PERCENT',
    'RAM_TOTAL',
    'RAM_AVAILABLE',
    'RAM_USED',
    'RAM_LIVRE',

    'SWAP_PERCENT',
    'SWAP_USADA',
    'SWAP_LIVRE',
    'SWAP_IN',
    'SWAP_OUT',

    'DISCO_PERCENT',
    'DISCO_USADO',
    'DISCO_LIVRE'
]

# Leitura do CSV
def ler_csv(nome_arquivo: str) -> list:
    dados = []

    with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
        leitor = csv.reader(
            arquivo,
            delimiter=';'
        )

        for linha in leitor:
            if len(linha) != len(cabecalho):
                continue

            registro = {}

            for i in range(len(cabecalho)):
                registro[cabecalho[i]] = linha[i]

            dados.append(registro)

    return dados

def main():
    dados = ler_csv('data.csv')

    if len(dados) == 0:
        print("Nenhum dado encontrado.")
        return

    ex.exibir_relatorio(dados)

main()
