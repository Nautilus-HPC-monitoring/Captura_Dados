# Nautilus Python - Captura de métricas

Script que coleta métricas da máquina (CPU, RAM, SWAP e disco) e envia para um bucket S3 em lotes de arquivos CSV.

Antes de coletar, o script autentica o usuário na API do Nautilus e só monitora os componentes cadastrados para a máquina (node) em que está rodando.

## Como funciona

1. O usuário informa email e senha no terminal.
2. O script envia email, senha e o hostname da máquina para a API (`POST /autenticacao`).
3. A API devolve o node e os componentes cadastrados (CPU, RAM, SWAP, DISCO). Só esses componentes são coletados; os demais ficam com valor 0.
4. A cada 10 segundos é feita uma coleta, guardada em memória.
5. A cada 6 coletas (cerca de 1 minuto) é gerado um CSV novo, enviado para o S3 e apagado da máquina local.

Os arquivos no S3 ficam particionados por máquina e data:

```
<FILE_KEY>/hostname=<hostname>/ano=AAAA/mes=MM/dia=DD/data_AAAAMMDD_HHMMSS.csv
```

Exemplo:

```
raw/hostname=isacardosods-vivobook/ano=2026/mes=10/dia=03/data_20261003_130000.csv
```

Cada envio é um arquivo novo e nenhum arquivo é sobrescrito. Os CSVs usam `;` como separador.

## Requisitos

- Python 3.12 ou superior (o código usa f-strings com aspas aninhadas; em versões anteriores, troque as aspas externas por aspas duplas)
- Linux recomendado (a métrica `iowait` da CPU só existe no Linux)
- API do Nautilus rodando em `http://localhost:3000`
- Banco de dados com a máquina cadastrada (veja a seção de autenticação)
- Bucket S3 criado e credenciais AWS válidas

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests psutil boto3 python-dotenv
```

## Configuração do `.env`

Crie um arquivo `.env` na mesma pasta do script, com o conteúdo abaixo:

```dotenv
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=
REGION_NAME=sua-regiao
BUCKET_NAME=nome-do-seu-bucket
FILE_KEY=raw
```

| Variável | Descrição |
|---|---|
| `AWS_ACCESS_KEY_ID` | Chave de acesso da AWS |
| `AWS_SECRET_ACCESS_KEY` | Chave secreta da AWS |
| `AWS_SESSION_TOKEN` | Token de sessão (obrigatório em credenciais temporárias, como as do AWS Academy) |
| `REGION_NAME` | Região do bucket (ex.: `us-east-1`) |
| `BUCKET_NAME` | Nome do bucket, sem `s3://` |
| `FILE_KEY` | Prefixo de destino dentro do bucket (ex.: `raw`) |

Atenção ao preencher:

- **`FILE_KEY` sem barra no começo e sem barra no final.** Com `/raw`, a chave vira `/raw/...` e o S3 cria um prefixo separado, com nome vazio. Use `raw`.
- **`BUCKET_NAME` é só o nome**, não a URL (`s3://`).
- Credenciais temporárias expiram. Se o envio começar a falhar, atualize as três variáveis `AWS_*` no `.env` e reinicie o script, porque o `.env` só é lido quando o programa inicia.
- **Nunca envie o `.env` para o Git.** Adicione ao `.gitignore`:
```
  .env
```

O arquivo `config_aws.py` carrega o `.env` e cria o `s3_client`. Ele precisa estar na mesma pasta do script.

## Autenticação

Ao iniciar, o script pede:

```
Email:
Senha:
```

Use o email institucional de um usuário cadastrado no sistema. O hostname **não é digitado**: o script pega o da máquina (`socket.gethostname()`) e a API procura esse hostname entre os nodes da empresa do usuário.

Para o login funcionar, é preciso que:

- o usuário exista na tabela `usuario`;
- o hostname da máquina esteja cadastrado na tabela `node`, dentro de um cluster da empresa do usuário;
- a máquina tenha componentes vinculados em `componente_node` (tipos `CPU`, `RAM`, `SWAP` e `DISCO`, escritos exatamente assim).

Para conferir o hostname da sua máquina:

```bash
python3 -c "import socket; print(socket.gethostname())"
```

O valor precisa ser idêntico ao que está na coluna `hostname` da tabela `node`.

## Executando

1. Suba a API do Nautilus (porta 3000).
2. Confira se o `.env` está preenchido.
3. Rode o script:

```bash
python3 captura.py
```

4. Informe email e senha.

Se a autenticação der certo, o terminal mostra as linhas coletadas a cada 10 segundos e uma mensagem a cada lote enviado:

```
Lote de 6 linhas enviado com sucesso!
```

Para encerrar, use `Ctrl+C`. As leituras que ainda não foram enviadas são enviadas antes de o script fechar.

## Configurações do script

No `captura.py`:

| Constante | Padrão | Descrição |
|---|---|---|
| `INTERVALO` | `10` | Segundos entre cada coleta |
| `LOTE` | `6` | Coletas por arquivo enviado |

Com os valores padrão, é gerado um arquivo por minuto.

## Verificando o envio

```bash
aws s3 ls s3://NOME-DO-BUCKET/raw/ --recursive --human-readable
```

## Problemas comuns

| Mensagem | Causa provável |
|---|---|
| `Cannot POST /autenticacao` | A rota não está registrada no `app.js` da API, ou o servidor não foi reiniciado |
| `Usuário não encontrado` | Email não cadastrado na tabela `usuario` |
| `Node não encontrado` | Hostname da máquina diferente do cadastrado na tabela `node` |
| `Não foi possível conectar à API` | A API não está rodando em `localhost:3000` |
| `Falha no envio` | Credenciais AWS expiradas, `BUCKET_NAME` vazio ou sem permissão no bucket. O erro detalhado aparece no log. As linhas não são perdidas e vão no próximo lote |
| `NameError: s3_client` | O `config_aws.py` não está na pasta do script ou não define o `s3_client` |
| Arquivo em prefixo errado no S3 | `FILE_KEY` com barra no começo ou no final |
| `AttributeError` em `cpu_freq` ou `iowait` | Algumas máquinas retornam `cpu_freq` vazio, e `iowait` só existe no Linux |