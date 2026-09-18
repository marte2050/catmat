# Projeto para busca de CATMAT/CATSERV

Esse projeto foi construído para buscar de forma automatizada os catmat/catserv com base no descritivo do material e serviço definido pelo usuário. Sem esse projeto as buscas eram feitas de forma manual, o que demandava muito tempo e esforço. Com a automatização, é possível realizar buscas mais rápidas e precisas, economizando tempo e recursos no processo de licitação além de poder ser integrado a outros sistemas de forma simples. A solução combina **busca híbrida** (semântica + lexical) sobre os dados do Compras.gov.br, permitindo encontrar o item mais próximo a partir de um descritivo textual, como *"computador com processador core i5, 8GB de RAM"*.

## Sumário

- [Arquitetura](#arquitetura)
- [Stack](#stack)
- [Pré-requisitos e configuração](#pré-requisitos-e-configuração)
- [Banco de dados e migrations](#banco-de-dados-e-migrations)
- [Ingestão (ETL)](#ingestão-etl)
- [Embeddings (Qdrant + FastEmbed)](#embeddings-qdrant--fastembed)
- [Referência da API do Compras.gov.br](#referência-da-api-do-comprasgovbr)

## Arquitetura

A arquitetura do sistema foi construído conforme diagrama abaixo:

![alt text](docs/camada_persistencia.png)

## Stack

| Camada | Tecnologia |
| --- | --- |
| Linguagem | Python 3.14 |
| API | FastAPI + Uvicorn |
| Banco relacional | PostgreSQL 13 (+ SQLAlchemy 2 async + asyncpg) |
| Migrations | Alembic |
| Banco vetorial | Qdrant |
| Embeddings locais | FastEmbed (ONNX): dense + sparse BM25 |
| HTTP client | httpx |
| CLI | Typer |
| Empacotamento | Poetry (`pyproject.toml`) |
| Infra | Docker Compose (+ Ofelia para agendamento) |

## Pré-requisitos e configuração

### Variáveis de ambiente (`.env`)

O projeto lê um arquivo `.env` na raiz. As principais variáveis (com os defaults):

| Variável | Default | Descrição |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://root:root@localhost:5432/catmat` | Conexão do Postgres |
| `COMPRAS_API_BASE_URL` | `https://dadosabertos.compras.gov.br/modulo-material/` | Base da API |
| `INGESTION_PAGE_SIZE` | `500` | Registros por página (10–500) |
| `INGESTION_CONCURRENCY` | `1` | Páginas buscadas em paralelo |
| `INGESTION_REQUEST_INTERVAL` | `0.5` | Intervalo mínimo entre requisições (s) |
| `INGESTION_BATCH_SIZE` | `1000` | Linhas por lote de upsert |
| `HTTP_TIMEOUT` | `60.0` | Timeout HTTP (s) |
| `HTTP_RETRIES` | `8` | Tentativas por página em caso de erro |
| `HTTP_BACKOFF_BASE` | `1.0` | Base do backoff exponencial |
| `HTTP_BACKOFF_MAX` | `60.0` | Teto do backoff |
| `EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | Modelo denso |
| `EMBEDDING_DIM` | `768` | Dimensão do vetor denso |
| `EMBEDDING_SPARSE_MODEL` | `Qdrant/bm25` | Modelo esparso |
| `EMBEDDING_LANGUAGE` | `portuguese` | Idioma do BM25 |
| `EMBEDDING_BATCH_SIZE` | `64` | Itens por lote de embedding |
| `EMBEDDING_MAX_CHARS` | `2000` | Truncamento do texto embedado |
| `QDRANT_URL` | `http://localhost:6333` | Endpoint do Qdrant |
| `QDRANT_COLLECTION_ITEMS` | `catmat_items` | Nome da coleção |


### Subindo a infraestrutura

```bash
docker compose -f devops/docker-compose.yaml up -d db qdrant
```

### Instalação

```bash
# Com Poetry (recomendado)
poetry install
source .venv/bin/activate
```

Ao instalar o pacote, ficam disponíveis os comandos de linha de comando `catmat-etl` e `catmat-embed`.

## Banco de dados e migrations


### Modelagem da tabela relacional

![Diagrama das tabelas](docs/diagram.png)


### Migrations (Alembic)

```bash
# aplicar
.venv/bin/alembic -c catmat/alembic.ini upgrade head

# ver revisão atual
.venv/bin/alembic -c catmat/alembic.ini current

# verificar se models e banco estão em sincronia
.venv/bin/alembic -c catmat/alembic.ini check

# criar nova migration por autogenerate
.venv/bin/alembic -c catmat/alembic.ini revision --autogenerate -m "descricao"
```

## Ingestão (ETL)

Para popular os dados podemos executar o CLI, ao qual irá buscar os dados partir da API de dados abertos do Compras.gov.br. É **idempotente** (upsert por chave natural) e **"retomável"**.

### Fontes

Abaixo uma perspectiva da quantidade de dados com base na última aferição.

| Loader | Endpoint | Registros |
| --- | --- | ---: |
| `groups` | `1_consultarGrupoMaterial` | 79 |
| `classes` | `2_consultarClasseMaterial` | 711 |
| `pdms` | `3_consultarPdmMaterial` | 20.433 |
| `items` | `4_consultarItemMaterial` | 344.984 |
| `expense-natures` | `5_consultarMaterialNaturezaDespesa` | 22 |
| `supply-units` | `6_consultarMaterialUnidadeFornecimento` | 38.096 |

### Comandos

```bash
# carga completa (ordem respeita as FKs)
.venv/bin/python -m catmat.etl sync all

# um recurso específico
.venv/bin/python -m catmat.etl sync items
.venv/bin/python -m catmat.etl sync expense-natures

# ajustes pontuais
.venv/bin/python -m catmat.etl sync items --page-size 500 --concurrency 1 \
  --request-interval 0.5 --max-retries 8 --batch-size 1000
.venv/bin/python -m catmat.etl sync items --limit-pages 2
```

Entre os parâmetros aceitos estão: `all`, `groups`, `classes`, `pdms`, `items`, `expense-natures`, `supply-units`.

## Embeddings (Qdrant + FastEmbed)

Para o processo de embeddings foi realizado um processo local e é concatenado os itens abaixo:

```
"{nome_grupo} | {nome_classe} | {nome_pdm} | {descrição_item}"
```

### Modelo e coleção

- **Denso**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (768d), buscado com prefixos de query/passage.
- **Esparso**: `Qdrant/bm25` (idioma português), com modificador **IDF** — cobre códigos/números exatos (ex.: `i5`, `8GB`, `127V`).
- Coleção `catmat_items` com vetores nomeados `dense` e `sparse`; `point id = item_code`; payload com códigos/nomes e índices para filtro (`group_code`, `pdm_code`, `item_status`).

### Incremental

Cada item guarda `content_hash` (sha256 do texto embedado). Numa reexecução, só são reembeddados os itens cujo texto mudou (ou que nunca foram embedados) — inclusive quando o nome de grupo/classe/PDM muda.

### Comandos

```bash
# carga completa (delta automático nas reexecuções)
.venv/bin/python -m catmat.embeddings sync items

# recriar a coleção do zero
.venv/bin/python -m catmat.embeddings sync items --recreate

# limitar para testes
.venv/bin/python -m catmat.embeddings sync items --limit 1000 --batch-size 64
```

### Desempenho

O embedding é feito localmente em CPU (FastEmbed/ONNX). Como referência, em uma máquina de 16 vCPU a vazão fica em torno de **~10–15 itens/s**, então a carga completa de ~345 mil itens leva de **~6 a 8 horas**. O processo é incremental, então interrupções podem ser retomadas executando o comando novamente.

## Referência da API do Compras.gov.br

O comprasnet utiliza o conceito de PDM - Padrão Descritivo de Materiais, que é uma forma de padronizar a descrição dos materiais e serviços, facilitando a busca e a identificação dos mesmos. O PDM encontra-se agrupado em grupos e classes. Nas subseções abaixo, detalhamos cada um desses elementos e como eles se relacionam.

A base dos endpoints é: `https://dadosabertos.compras.gov.br/modulo-material/`.

### Grupos

Os grupos são a primeira camada do PDM e representam uma categoria ampla de materiais ou serviços. Cada grupo possui os seguintes atributos:

| Nome do Campo | Descrição |
| --- | --- |
| **codigoGrupo** | Um identificador único para o grupo. |
| **nomeGrupo** | Nome do grupo. |
| **statusGrupo** | Situação do grupo (ativo ou inativo). |
| **dataHoraAtualizacao** | Data e hora em que o grupo foi atualizado. |

Para fazer a busca de grupos podemos usar a URI `https://dadosabertos.compras.gov.br/modulo-material/1_consultarGrupoMaterial` da API do comprasnet, que retorna uma lista de grupos disponíveis.

### Classes

As classes são a segunda camada do PDM e representam uma subcategoria dentro de um grupo. Cada classe possui os seguintes atributos:

| Nome do Campo | Descrição |
| --- | --- |
| **codigoClasse** | Um identificador único para a classe. |
| **codigoGrupo** | O código do grupo ao qual a classe pertence. |
| **nomeGrupo** | Nome do grupo. |
| **nomeClasse** | Nome da classe. |
| **statusClasse** | Situação da classe (ativo ou inativo). |
| **dataHoraAtualizacao** | Data e hora em que a classe foi atualizada. |

Para fazer a busca de classes podemos usar a URI `https://dadosabertos.compras.gov.br/modulo-material/2_consultarClasseMaterial` da API do comprasnet, que retorna uma lista de classes disponíveis.

### PDMs

Os PDMs são um conjunto de regras, características e valores usado para organizar e padronizar o cadastro de itens e produtos.

| Nome do Campo | Descrição |
| --- | --- |
| **codigoGrupo** | Código do grupo. |
| **nomeGrupo** | Nome do grupo. |
| **codigoClasse** | Código da classe. |
| **nomeClasse** | Nome da classe. |
| **codigoPdm** | Código do PDM. |
| **nomePdm** | Nome do PDM. |
| **statusPdm** | Situação do PDM (ativo ou inativo). |
| **dataHoraAtualizacao** | Data e hora em que o PDM foi atualizado. |

Para fazer a busca de PDMs podemos usar a URI `https://dadosabertos.compras.gov.br/modulo-material/3_consultarPdmMaterial` da API do comprasnet, que retorna uma lista de PDMs disponíveis.

### Catmats

Os catmats são a camada final do PDM e representam os materiais cadastrados no sistema. Cada catmat possui os seguintes atributos:

| Nome do Campo | Descrição |
| --- | --- |
| **codigoItem** | Um identificador único para o catmat. |
| **codigoGrupo** | Código do grupo ao qual o catmat pertence. |
| **nomeGrupo** | Nome do grupo. |
| **codigoClasse** | Código da classe ao qual o catmat pertence. |
| **nomeClasse** | Nome da classe. |
| **codigoPdm** | Código do PDM ao qual o catmat pertence. |
| **nomePdm** | Nome do PDM. |
| **descricaoItem** | Descrição detalhada do catmat. |
| **statusItem** | Situação do catmat (ativo ou inativo). |
| **itemSustentavel** | Indica se o catmat é sustentável ou não. |
| **codigo_ncm** | Código de NCM - Nomenclatura Comum do Mercosul. |
| **descricao_ncm** | Descrição do NCM. |
| **aplica_margem_preferencia** | Indica se o catmat aplica margem de preferência ou não. |
| **dataHoraAtualizacao** | Data e hora em que o catmat foi atualizado. |

Para fazer a busca de catmats podemos usar a URI `https://dadosabertos.compras.gov.br/modulo-material/4_consultarItemMaterial` da API do comprasnet, que retorna uma lista de catmats disponíveis.

### Natureza de despesa

A natureza de despesa é um código que identifica a categoria de gasto associada a um PDM. Cada natureza de despesa possui os seguintes atributos:

| Nome do Campo | Descrição |
| --- | --- |
| **codigoPdm** | Código do PDM ao qual a natureza de despesa pertence. |
| **codigoNaturezaDespesa** | Código único da natureza de despesa. |
| **nomeNaturezaDespesa** | Nome da natureza de despesa. |
| **statusNaturezaDespesa** | Situação da natureza de despesa (ativo ou inativo). |

Para fazer a busca de natureza de despesa podemos usar a URI `https://dadosabertos.compras.gov.br/modulo-material/5_consultarMaterialNaturezaDespesa` da API do comprasnet, que retorna uma lista de naturezas de despesa disponíveis.

### Unidade de Fornecimento

A unidade de fornecimento é um código que identifica a unidade de medida associada a um PDM. Cada unidade de fornecimento possui os seguintes atributos:

| Nome do Campo | Descrição |
| --- | --- |
| **codigoPdm** | Código do PDM ao qual a unidade de fornecimento pertence. |
| **siglaUnidadeFornecimento** | Sigla da unidade de fornecimento. |
| **nomeUnidadeFornecimento** | Nome da unidade de fornecimento. |
| **descricaoUnidadeFornecimento** | Descrição detalhada da unidade de fornecimento. |
| **siglaUnidadeMedida** | Sigla da unidade de medida. |
| **capacidadeUnidadeFornecimento** | Capacidade da unidade de fornecimento. |
| **numeroSequencialUnidadeFornecimento** | Número sequencial da unidade de fornecimento. |
| **statusUnidadeFornecimentoPdm** | Situação da unidade de fornecimento no PDM (ativo ou inativo). |
| **statusUnidadeFornecimento** | Situação da unidade de fornecimento (ativo ou inativo). |
| **dataHoraAtualizacao** | Data e hora em que a unidade de fornecimento foi atualizada. |

Para fazer a busca de unidade de fornecimento podemos usar a URI `https://dadosabertos.compras.gov.br/modulo-material/6_consultarMaterialUnidadeFornecimento` da API do comprasnet, que retorna uma lista de unidades de fornecimento disponíveis.

### Paginação e volumes

Todas as rotas de `modulo-material` retornam um envelope JSON com o campo `resultado` (lista de registros) e os campos de paginação `totalRegistros`, `totalPaginas` e `paginasRestantes`. A paginação é feita pelos parâmetros de query `pagina` (número da página, iniciando em 1) e `tamanhoPagina` (quantidade de registros por página, no intervalo de **10 a 500**; o valor padrão é 10).

Os volumes observados na API são:

| Recurso | Endpoint | Registros | Páginas com `tamanhoPagina=500` |
| --- | --- | ---: | ---: |
| Grupos | `1_consultarGrupoMaterial` | 79 | 1 |
| Classes | `2_consultarClasseMaterial` | 711 | 2 |
| PDMs | `3_consultarPdmMaterial` | 20.433 | 41 |
| Catmats | `4_consultarItemMaterial` | 344.984 | 690 |
| Natureza de despesa | `5_consultarMaterialNaturezaDespesa` | 22 | 3 |
| Unidade de fornecimento | `6_consultarMaterialUnidadeFornecimento` | 38.096 | 77 |

