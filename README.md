# Plataforma MB

Sistema interno de gestão patrimonial e imobiliária de uma holding familiar. Centraliza o controle de imóveis, contratos, inquilinos, documentos, lembretes e financeiro — substituindo planilhas e arquivos dispersos por uma interface web auditável e de baixa manutenção.

---

## Para quem não é técnico

O sistema funciona como um painel de controle acessível pelo navegador. Nele é possível:

- Cadastrar e acompanhar imóveis (localização, área, valor de mercado, participação de cada proprietário)
- Gerenciar contratos de aluguel com inquilinos, incluindo histórico de preços e status automático (Ativo, Vencido, Renovado etc.)
- Armazenar documentos de qualquer entidade (imóvel, contrato, pessoa) com categorização por tipo
- Manter um cadastro unificado de pessoas — uma mesma pessoa pode ser proprietária, inquilina e fiadora ao mesmo tempo, sem duplicação de dados
- Receber lembretes automáticos de prazos críticos: reajuste anual, renovação de contrato, IPTU, seguro-fiança, carnê-leão

O sistema foi projetado para operar de forma autônoma com mínima manutenção, mesmo com o responsável em fuso horário diferente (Toronto, UTC-5).

---

## Stack técnica

| Camada | Tecnologia |
|---|---|
| Backend | Django 5.2 + Django Unfold (admin aprimorado) |
| Banco de dados | Neon Postgres (cloud, com PITR) |
| Arquivos / documentos | Cloudflare R2 (S3-compatible, zero egress) |
| Hospedagem | Railway (deploy via `git push`, sem cold start) |
| Tarefas agendadas | Railway cron jobs → Django management commands |
| Autenticação | Django auth nativo (usuários internos apenas) |

**Custo alvo: US$ 0/mês** (dentro dos tiers gratuitos de Neon e R2, e do crédito mensal do Railway).

---

## Arquitetura geral

```
plataforma-mb/
├── config/          # settings, urls, wsgi, utils globais, dynamic_form
├── core/            # Tarefa / Lembrete (GenericFK)
├── pessoas/         # Pessoa + Perfis (Proprietário, Cliente, Imobiliária, Fiador)
├── imoveis/         # Imóvel, ImovelProprietario, características por tipo
├── contratos/       # Contrato, Garantia, histórico de preços
├── documentos/      # Documento (GenericFK), upload R2, metadados por tipo
├── planejamento/    # Documentação de negócio (HTML/MD)
└── templates/       # Templates Django (admin overrides)
```

O admin do Django (com tema Unfold) é a interface principal. Não há frontend separado.

---

## Domínio e modelos principais

### Pessoas — padrão Party + Perfis

Uma única model `Pessoa` (CPF/CNPJ único, apenas dígitos no banco) pode ter múltiplos perfis simultâneos:

- `PerfilProprietario` — com flag `interno` para distinguir membros da holding
- `PerfilCliente` (inquilino)
- `PerfilImobiliaria`
- `PerfilFiador`

FKs de outras models apontam **sempre para o perfil**, nunca para `Pessoa` diretamente — os dropdowns ficam restritos ao papel correto. Soft delete via campo `ativo`; nunca delete físico (exigência de auditoria/IR).

### Imóveis

- Múltiplos proprietários via through model `ImovelProprietario` com campo `participacao` (Decimal, soma ≤ 1)
- `caracteristicas` JSONField com schema por tipo de imóvel (apartamento tem `andar` e `area_privativa`; terreno tem `area_terreno` e `testada` etc.)
- Campos calculados como `@property`: `valor_por_m2`, `participacao_interna_pct`, `valor_interno`
- Status `GESTAO_TERCEIRO` para imóveis administrados por terceiros sem contrato direto

### Contratos

- `vigencia` em meses + `renovacao_automatica`
- `data_fim` e `status` como `@property` (nunca persistidos)
- Status possíveis: Futuro / Ativo / Renovado / Vencido / Rescindido
- `historico_precos` detecta mudanças de `valor_aluguel` via `django-simple-history`
- Garantia com `CASCADE` ao contrato; tipos: FIADOR / DEPOSITO / SEGURO / SEM_GARANTIA

### Documentos

- Model genérica com `GenericForeignKey` — um único cadastro cobre documentos de qualquer entidade
- `METADADOS_SCHEMA` define campos específicos por tipo (ex: `numero_apolice` para seguro)
- Upload path dinâmico: `{entidade}/{tipo-pasta}/{YYYY.MM.DD} - {tipo} - {nome}{ext}`
- Admin com selects em cascata: entidade → objeto → tipo → campos específicos (via AJAX + Alpine.js)
- Novas entidades com `GenericRelation(Documento)` aparecem no select automaticamente, sem alteração manual

---

## Deploy

O deploy é automático a cada `git push` para `main`. O Railway detecta o projeto Python via Nixpacks e executa na ordem:

```
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi --bind 0.0.0.0:$PORT
```

Arquivos estáticos são servidos pelo Whitenoise. Arquivos de upload vão direto para o R2.

---

## Configuração local

### Pré-requisitos

- Python 3.12+
- Postgres local (ou usar `DATABASE_URL` apontando para Neon)

### Setup

```bash
git clone <repo>
cd plataforma-mb

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env   # preencher variáveis abaixo

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Variáveis de ambiente necessárias

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` em dev, `False` em produção |
| `DATABASE_URL` | URL de conexão Postgres (ex: `postgresql://user:pass@host/db`) |
| `AWS_ACCESS_KEY_ID` | R2 Access Key (opcional em dev) |
| `AWS_SECRET_ACCESS_KEY` | R2 Secret Key (opcional em dev) |
| `AWS_STORAGE_BUCKET_NAME` | Nome do bucket R2 |
| `AWS_S3_ENDPOINT_URL` | Endpoint R2 (`https://<account>.r2.cloudflarestorage.com`) |
| `ALLOWED_HOSTS` | Hosts permitidos (separados por vírgula) |

Sem as variáveis `AWS_*`, o sistema usa armazenamento local (`MEDIA_ROOT`), adequado para desenvolvimento.

---

## Padrões de desenvolvimento

- **Antes de migrations:** sempre rodar `python manage.py check` com o venv ativo
- **Enums:** usar `TextChoices` — não criar models separadas para status/tipo
- **Campos calculados:** sempre como `@property`, nunca persistidos
- **Moeda:** usar `formatar_moeda(valor)` de `config/utils.py` em todo `@admin.display`
- **Soma de meses em datas:** usar `add_months(d, months)` de `config/utils.py`
- **Widgets:** subclassear `UnfoldAdminTextInputWidget` (não `TextInput`) para manter estilização Tailwind
- **Histórico:** `django-simple-history` em `Contrato`, `Imovel` e `Pagamento`
- **Alpine.js:** usar `x-model.fill` (não `x-model`) em selects cujo valor é renderizado pelo Django — evita que o Alpine sobrescreva o valor com `null` ao abrir um registro existente

---

## Roadmap

| Fase | Status |
|---|---|
| Fase 0 — Setup (Railway, Neon, Unfold) | ✅ Concluída |
| Fase 1 — Pessoas e Perfis | ✅ Concluída |
| Fase 2 — Imóveis e Proprietários | ✅ Concluída |
| Fase 3 — Contratos e Garantias | ✅ Concluída |
| Fase 4 — Documentos (GenericFK, R2, Alpine.js) | ✅ Concluída |
| Fase 5 — Lembretes e crons (Railway) | Em andamento |
| Fase 6 — Relatórios (IR, patrimonial, DRE) | Planejado |

**Backlog pós-MVP:** módulo financeiro, módulo de manutenção, validação de dígitos verificadores CPF/CNPJ, reajuste automático via API do BACEN, geração de recibo em PDF, dashboard fora do admin.

---

## Licença

Uso interno — todos os direitos reservados.
