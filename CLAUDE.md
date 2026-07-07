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

`pessoas`, `imoveis`, `contratos`, `financeiro`, `documentos`, `core` (Tarefa/Lembrete).

`core/admin.py` registra `User` e `Group` com `ModelAdmin` do Unfold (substituindo os defaults do Django) e restringe visibilidade na sidebar a superusuários via `permission_superuser` em `config/unfold_config.py`.

## Domínio

**Entidades principais:** Imóvel, Contrato, Inquilino, Pagamento, Documento, Manutenção, Tarefa/Lembrete.

**Prazos críticos:** reajuste anual (IGPM/IPCA), renovação de contrato, parcelas do IPTU, seguro-fiança, carnê-leão mensal (DARF), ajuste IRPF.

**Custom actions no admin:** calcular reajuste pelo índice vigente, gerar recibo do mês, exportar relatório para IR, relatório patrimonial consolidado.

## Padrões de modelagem

### Pessoas: pattern Party + Perfis

Uma pessoa (PF ou PJ) pode exercer múltiplos papéis simultaneamente (mesmo CPF/CNPJ pode ser proprietário, imobiliária, cliente e fiador).

- Model única `Pessoa` com dados comuns (nome, CPF/CNPJ `unique=True`, contato, endereço, tipo PF/PJ).
- Cada papel é um `Perfil*` separado com `OneToOneField` para `Pessoa`. MVP tem 4 perfis: `PerfilProprietario`, `PerfilCliente`, `PerfilImobiliaria`, `PerfilFiador`. `PerfilConstrutora` está no backlog.
- Cada perfil carrega **apenas** os campos específicos daquele papel.
- `cpf_cnpj` persiste **apenas dígitos** no banco (11=CPF, 14=CNPJ), campo opcional (`blank=True`). Formatação e máscara progressiva feitas via `CpfCnpjWidget` + `CpfCnpjField` em `pessoas/widgets.py` e `pessoas/forms.py`.
- `PerfilProprietario` tem flag `interno` (BooleanField) para distinguir membros da família/holding de terceiros.
- FKs de outras models apontam para o **perfil**, nunca para `Pessoa` direto. Ex.: `Contrato.cliente → PerfilCliente`. Isso restringe os dropdowns aos papéis corretos.
- `on_delete=PROTECT` em todas as FKs de perfis — nunca apagar pessoas com histórico (exigência IR/auditoria).
- Soft delete em `Pessoa` via campo `ativo`. Nunca delete físico.
- No admin (Unfold): `PessoaAdmin` usa `get_inlines()` para expor apenas os perfis que a pessoa já possui (não mostra inline de perfil que não existe). Todos os inlines de perfil e documentos têm `tab = True`. Admins próprios por perfil para visões dedicadas ("Imobiliárias", "Clientes" etc).

### Utilitários e padrões de exibição

- **Formatação de moeda:** `formatar_moeda(valor)` em `config/utils.py` — usar em todos os `@admin.display` que exibem R$. Retorna `'—'` para `None`.
- **Adição de meses a datas:** `add_months(d, months)` em `config/utils.py` — soma meses a uma `date` ajustando o dia ao último do mês quando necessário (ex: 31/jan + 1 mês → 28/fev). Usar sempre que precisar calcular prazo em meses.
- **Widgets customizados:** sempre subclassear `UnfoldAdminTextInputWidget` (não `TextInput`) para manter a estilização Tailwind do Unfold.
- **Datalist dinâmico:** campos com sugestões baseadas em dados existentes usam `<datalist>` + JS estático (ver `imoveis/widgets.py` — `EstadoWidget` com UFs estáticos, `MunicipioWidget` filtrado por estado via JSON injetado no DOM, JS em `imoveis/static/imoveis/js/municipio_estado_filter.js`).
- **Totais na listagem:** usar `list_after_template` + override de `changelist_view` para injetar totais no contexto (ver `ImovelAdmin`).
- **Unfold tabs:** fieldsets com `'classes': ['tab']` são agrupados num bloco de tabs. Fieldsets **sem** essa classe são renderizados **fora** do bloco (sempre antes), independente da posição na lista. Se um fieldset precisa aparecer depois das tabs, torná-lo tab também.

### Outros padrões

- **Múltiplos proprietários por imóvel** via through model `ImovelProprietario` com campo `participacao` (Decimal). `clean()` valida que a soma não ultrapassa 1 (validação de exatamente = 1 no nível do `Imovel.clean()` está no backlog).
- **Participação interna** calculada via `@property participacao_interna_pct` (soma dos proprietários com `interno=True`) e `@property valor_interno` (`valor_mercado × participacao_interna_pct`).
- **Campos calculados** (% do valor de mercado, R$/m², valor líquido estimado) sempre como `@property`. Nunca persistir.
- **Enums fixos** via `TextChoices`. Não criar models separadas para status/tipo/categoria.
- **Histórico de alterações** em `Contrato`, `Imovel` e `Pagamento` via `django-simple-history`.
- **Contrato:** vigência em meses (`vigencia` IntegerField) + `renovacao_automatica` + `quant_renov_automaticas`. `data_fim` e `status` como `@property` (nunca persistidos). `status` retorna: Futuro / Ativo / Renovado / Vencido / Rescindido. `historico_precos` como `@property` detecta mudanças de `valor_aluguel` via `HistoricalRecords`. FKs: `imovel → Imovel`, `cliente → PerfilCliente`, `imobiliaria → PerfilImobiliaria` (opcional).
- **Garantia:** `CASCADE` em relação ao contrato (garantia não existe sem contrato). Tipos: FIADOR / DEPOSITO / SEGURO / SEM_GARANTIA. FK `fiador → PerfilFiador` obrigatória apenas quando tipo = FIADOR (validado em `clean()`).
- **Imovel.Status** inclui `GESTAO_TERCEIRO` ('GT') para imóveis administrados por terceiros sem contrato direto.
- **Imovel.municipio** (campo renomeado de `cidade` em 2025-05): CharField com sugestões via `MunicipioWidget` (datalist dinâmico filtrado por estado). `quartos` e `vagas` removidos como campos fixos — estão no `CARACTERISTICAS_SCHEMA`.
- **Imovel.caracteristicas** JSONField com `CARACTERISTICAS_SCHEMA` na model — campos específicos por tipo de imóvel (ex: `andar`, `area_privativa` para apartamento; `area_terreno`, `testada` para terreno).
- **Documentos** via model genérica com `GenericForeignKey` — não uma model de documento por entidade relacionada. `METADADOS_SCHEMA` na model `Documento` define campos específicos por tipo (ex: `numero_apolice` para seguro). Upload path dinâmico: `{entidade}/{tipo-pasta}/{YYYY.MM.DD} - {tipo} - {nome}{ext}`. Storage: Cloudflare R2 via `django-storages[boto3]`, configurado condicionalmente em `settings.py` (ativo apenas quando variáveis `AWS_*` estão presentes). `GenericRelation` em `Imovel`, `Contrato`, `Pessoa` e todos os `Perfil*`.
- **DocumentoAdmin com GenericFK interativa:** selects em cascata — entidade → objeto → tipo → campos específicos. Entidades descobertas automaticamente via introspecção de `GenericRelation(Documento)` (novos models com essa relação aparecem no select sem alteração manual). `TIPOS_POR_ENTIDADE` em `documentos/admin.py` é a fonte única de quais tipos são permitidos por entidade; inlines referenciam esse dict. View AJAX em `/documentos/ajax/objetos/?ct=<id>` retorna objetos e tipos filtrados. JS em `documentos/static/documentos/js/documento_form.js` gerencia a cascata e preserva valores na edição.
- **Campos dinâmicos por tipo em formulários admin:** padrão reutilizável em `config/dynamic_form.py`. `DynamicSchemaFormMixin` no ModelForm lê um schema dict e cria campos `meta_*` dinamicamente, popula do JSONField na edição e salva de volta. `DynamicSchemaAdminMixin` no ModelAdmin resolve o conflito com `modelform_factory`; suporta `_extra_form_fields` para excluir campos não-model (ex: `entidade`, `objeto` do DocumentoAdmin). `build_conditional_fields(schema)` gera o dict `conditional_fields` do Unfold com expressões Alpine.js `x-show`. O campo discriminador usa `x-model.fill` (não `x-model`) para que Alpine leia o valor já renderizado pelo Django ao abrir um registro existente — sem o `.fill`, o Unfold inicializa `x-data` com `null` e o Alpine sobrescreve o select, ocultando todos os campos. Usado em `documentos` (metadados) e `imoveis` (características).

## Roadmap MVP

Ordem de implementação acordada (~13-20 dias com dedicação parcial):

- **Fase 0 — Setup:** projeto Django + Unfold, Neon via `DATABASE_URL`, deploy inicial Railway, env vars. ✅
- **Fase 1 — Pessoas (PES):** `Pessoa` com `cpf_cnpj` único (dígitos), 4 `Perfil*` MVP via OneToOne, máscara CPF/CNPJ no widget, admin com inlines dinâmicos por perfil existente + admins próprios por perfil, soft delete via `ativo`. ✅
- **Fase 2 — Imóveis (PAT):** `Imovel` + through `ImovelProprietario`, `clean()` valida soma ≤ 1, `@property` calculadas (`valor_por_m2`, `participacao_interna_pct`, `valor_interno`), django-simple-history. ✅
- **Fase 3 — Contratos (CON):** `Contrato` + `Garantia`, histórico de auditoria, status calculado, custom actions (reajuste IGPM/IPCA, recibo PDF). ✅ (reajuste e recibo PDF → backlog)
- **Fase 4 — Documentos (DOC):** `Documento` com `GenericForeignKey`, `METADADOS_SCHEMA` com campos específicos por tipo, upload R2, inlines filtrados por tipo em cada entidade, admin com GenericFK interativa (entidade→objeto→tipo) e campos dinâmicos via Alpine.js. `DynamicSchemaFormMixin` / `DynamicSchemaAdminMixin` em `config/dynamic_form.py`. `Imovel.CARACTERISTICAS_SCHEMA` + `caracteristicas` JSONField; campo `municipio` (renomeado de `cidade`). ✅
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
- Sempre rodar `python manage.py check` antes de `makemigrations`. Venv em `.venv/bin/activate`.
