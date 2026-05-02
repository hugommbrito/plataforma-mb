# Plataforma MB

Sistema de gerenciamento de imóveis e patrimônios de uma holding familiar. Cobre contratos, dados de imóveis, inquilinos, documentos, patrimônio, lembretes e financeiro.

Uso interno familiar (baixo volume). Responsável mora em Toronto (UTC-5), então o sistema precisa operar de forma autônoma com mínima manutenção.

## Stack

- **Backend:** Django + Django Unfold (aproveita o Django Admin para CRUD, filtros, permissões e audit trail)
- **Banco:** Neon Postgres (free/Launch — PITR cobre backup)
- **Arquivos:** Cloudflare R2 via `django-storages` (S3-compatible, zero egress)
- **Hospedagem:** Railway (sem cold start, deploy via git push, US$ 5/mês de crédito)
- **Scheduled tasks:** Railway cron jobs chamando Django management commands
- **Custo alvo:** US$ 0/mês

Não sugerir alternativas serverless (Vercel), AWS direto, OneDrive ou banco local — já foram avaliadas e descartadas.

## Deploy (Railway)

O deploy é disparado automaticamente a cada `git push` para `main`. O Railway usa Nixpacks para detectar o projeto Python e instalar o `requirements.txt` na fase de build.

O start command definido em `railway.json` executa três etapas em sequência:

1. `collectstatic --noinput` — copia os arquivos estáticos (CSS/JS do Unfold e do admin) para `staticfiles/`, de onde o Whitenoise os serve em produção.
2. `migrate` — aplica migrations pendentes no Neon Postgres antes de subir o servidor.
3. `gunicorn config.wsgi --bind 0.0.0.0:$PORT` — inicia o servidor WSGI na porta dinâmica injetada pelo Railway (`$PORT`).

## Modelo operacional

Híbrido: administradora local cuida do dia-a-dia. O sistema cobre a camada estratégica — patrimônio, documentos, financeiro consolidado, IR e prazos.

## Apps Django

`pessoas`, `imoveis`, `contratos`, `financeiro`, `documentos`.

## Domínio

**Entidades principais:** Imóvel, Contrato, Inquilino, Pagamento, Documento, Manutenção, Tarefa/Lembrete.

**Prazos críticos:** reajuste anual (IGPM/IPCA), renovação de contrato, parcelas do IPTU, seguro-fiança, carnê-leão mensal (DARF), ajuste IRPF.

**Custom actions no admin:** calcular reajuste pelo índice vigente, gerar recibo do mês, exportar relatório para IR, relatório patrimonial consolidado.

## Padrões de modelagem

### Pessoas: pattern Party + Perfis

Uma pessoa (PF ou PJ) pode exercer múltiplos papéis simultaneamente (mesmo CPF/CNPJ pode ser proprietário, imobiliária, cliente e fiador).

- Model única `Pessoa` com dados comuns (nome, CPF/CNPJ `unique=True`, contato, endereço, tipo PF/PJ).
- Cada papel é um `Perfil*` separado (`PerfilProprietario`, `PerfilCliente`, `PerfilImobiliaria`, `PerfilFiador`, `PerfilConstrutora`) com `OneToOneField` para `Pessoa`.
- Cada perfil carrega **apenas** os campos específicos daquele papel (ex.: `taxa_administracao` só em `PerfilImobiliaria`; `comprovante_renda` só em `PerfilFiador`).
- FKs de outras models apontam para o **perfil**, nunca para `Pessoa` direto. Ex.: `Contrato.cliente → PerfilCliente`. Isso restringe os dropdowns aos papéis corretos.
- `on_delete=PROTECT` em todas as FKs de perfis — nunca apagar pessoas com histórico (exigência IR/auditoria).
- Soft delete em `Pessoa` via campo `ativo`. Nunca delete físico.
- No admin (Unfold): perfis como `StackedInline` em `PessoaAdmin` + `ModelAdmin` próprio para visões dedicadas ("Imobiliárias", "Clientes" etc).

### Outros padrões

- **Múltiplos proprietários por imóvel** via through model `ImovelProprietario` com campo `participacao` (Decimal). `clean()` valida que a soma das participações de um imóvel = 1.
- **Campos calculados** (% do valor de mercado, R$/m², valor líquido estimado) sempre como `@property`. Nunca persistir.
- **Enums fixos** via `TextChoices`. Não criar models separadas para status/tipo/categoria.
- **Histórico de alterações** em `Contrato`, `Imovel` e `Pagamento` via `django-simple-history` ou `django-auditlog`.
- **Documentos** via model genérica com `GenericForeignKey` — não uma model de documento por entidade relacionada.

## Roadmap MVP

Ordem de implementação acordada (~13-20 dias com dedicação parcial):

- **Fase 0 — Setup:** projeto Django + Unfold, Neon via `DATABASE_URL`, deploy inicial Railway, env vars. ✅
- **Fase 1 — Pessoas (PES):** `Pessoa` com `cpf_cnpj` único, 5 `Perfil*` via OneToOne, admin com inlines + admins próprios por perfil, soft delete via `ativo`.
- **Fase 2 — Imóveis (PAT):** `Imovel` + through `ImovelProprietario`, validação `clean()` da soma de participações = 1, `@property` calculadas, django-simple-history.
- **Fase 3 — Contratos (CON):** `Contrato` + `Garantia`, histórico de auditoria, status calculado, custom actions (reajuste IGPM/IPCA, recibo PDF).
- **Fase 4 — Documentos (DOC):** configurar `django-storages` com Cloudflare R2 (instalar lib, variáveis `AWS_*` no `.env`/Railway, `DEFAULT_FILE_STORAGE`), `Documento` com `GenericForeignKey`, upload R2, URLs assinadas, inlines no admin das entidades relacionadas.
- **Fase 5 — Lembretes (LEM):** `Tarefa` com GenericFK, 6 management commands, Railway crons, e-mail SMTP simples.
- **Fase 6 — Relatórios (REL):** custom actions — patrimonial consolidado, rendimentos por CPF (IR), DRE por imóvel.

Pós-MVP (backlog): épicos `financeiro` e `manutencao`, notificações além de e-mail, dashboard fora do admin.

Detalhamento completo em [planejamento.html](planejamento.html) e [historias_usuario.md](historias_usuario.md).

## Diretrizes para sugestões

- Soluções compatíveis com Django + Unfold + Neon + R2 + Railway.
- Priorizar **baixa manutenção** sobre otimizações prematuras.
- Código em Python/Django salvo pedido explícito em contrário.
- Considerar produção em Railway + Neon + R2 ao propor configurações.
- Automações e tarefas agendadas: primeira escolha são **migrations** e **management commands** (acionados por Railway cron).
