# Plano: UX/Admin Unfold — Configuração completa

## Context

O Unfold está instalado mas opera com defaults — sem `UNFOLD = {}` em settings, sem sidebar customizada, sem dashboard, e com admins usando HTML manual em vez dos utilitários semânticos do Unfold. O objetivo é implementar as melhorias do `planejamento/plano-ux-admin.md` com os arquivos existentes. O `core` app (Tarefa) não existe ainda (é Fase 5), então os itens que dependem dele ficam diferidos.

---

## Estado atual (o que está faltando)

| Arquivo | Status atual |
|---|---|
| `config/settings.py` | Sem `UNFOLD = {}`, `TEMPLATES DIRS: []` vazio |
| `core/` app | Não existe (criar minimalista — sem models) |
| `templates/admin/index.html` | Não existe |
| `contratos/admin.py` | `status_display` usa `format_html` com cores manuais; sem tabs; sem Unfold decorators |
| `documentos/admin.py` | Sem badge de vencimento; sem Unfold decorators |
| `imoveis/admin.py` | `status` raw na list_display (sem badge); `registro_regularizado_display` já usa `display_for_label` corretamente |

O template `imoveis/templates/admin/imoveis/imovel/change_list_after.html` **já existe** e funciona.

---

## Arquivo 1 — `config/settings.py`

### 1a. TEMPLATES DIRS
```python
'DIRS': [BASE_DIR / 'templates'],  # linha 75
```

### 1b. Importar UNFOLD do arquivo dedicado (ao final do settings.py)
```python
from config.unfold_config import UNFOLD  # noqa: E402
```
Sem adicionar mais nada no settings.py — toda a config do Unfold fica isolada em `config/unfold_config.py`.

### 1c. Adicionar `'core'` em INSTALLED_APPS
```python
'core',
```

---

## Arquivo 1b — `config/unfold_config.py` (criar)

Arquivo dedicado exclusivamente à configuração do Unfold, sem poluir o settings.py.

```python
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
```

Contém:
- `badge_contratos_vencendo(request)` — conta contratos vencendo em 60 dias
- `environment_callback(request)` — badge Produção/Local
- `UNFOLD = {}` completo

**Sidebar sections:**
- Visão Geral → Dashboard
- Patrimônio → Imóveis, Contratos (badge vencendo), Documentos
- Pessoas → Todas, Inquilinos, Proprietários, Imobiliárias, Fiadores
- *(sem Operacional/Tarefas — Fase 5)*

**Referências de string no dict** apontam para este arquivo (exceto o dashboard):
- `"ENVIRONMENT": "config.unfold_config.environment_callback"`
- `"badge": "config.unfold_config.badge_contratos_vencendo"`
- `"DASHBOARD_CALLBACK": "core.views.dashboard_callback"`

**Referência:** `planejamento/plano-ux-admin.md` linhas 27-149 (adaptar: remover `core_tarefa`, ajustar strings de callback para `config.unfold_config.*` e `core.views.*`)

---

## Arquivo 2 — `core` app (criar, minimalista)

`config/` é o pacote de projeto (settings, urls, wsgi) — não é o lugar para views de negócio. O CLAUDE.md já prevê `core` como app do sistema. Criar agora de forma minimalista mantém a arquitetura consistente e evita mover arquivos quando a Fase 5 implementar o model `Tarefa`.

**Arquivos a criar:**
- `core/__init__.py` — vazio
- `core/apps.py` — AppConfig padrão
- `core/views.py` — `dashboard_callback`

### `core/views.py`
`dashboard_callback(request, context)` com KPIs de imóveis:
- `total_imoveis`, `imoveis_alugados`, `valor_interno_total`
- `chart_status` (JSON para gráfico de barras por status do imóvel)
- *(sem `tarefas_urgentes` — Fase 5)*

Importa apenas `from imoveis.models import Imovel`.

No `unfold_config.py`, a referência fica como estava no plano original:
```python
"DASHBOARD_CALLBACK": "core.views.dashboard_callback"
```

---

## Arquivo 3 — `templates/admin/index.html` (criar, diretório novo)

Dashboard com:
- 3 cards KPI (imóveis total, alugados, valor interno)
- Gráfico de barras `{% component "unfold/components/chart/bar.html" ... %}`
- *(sem seção de tarefas — Fase 5)*

Referência: `planejamento/plano-ux-admin.md` linhas 207-258 (adaptar: remover bloco de tarefas urgentes)

---

## Arquivo 4 — `contratos/admin.py`

### O que muda
1. Adicionar `from unfold.decorators import display` no topo
2. Adicionar `compressed_fields = True`, `warn_unsaved_form = True`, `list_fullwidth = True` em `ContratoAdmin`
3. Substituir `@admin.display` por `@display(label={...})` em `status_display`:
   ```python
   @display(description='Status', label={
       'Ativo': 'success', 'Renovado': 'success',
       'Futuro': 'info', 'Vencido': 'danger', 'Rescindido': 'default',
   })
   def status_display(self, obj):
       return obj.status  # sem format_html, o label faz o badge
   ```
4. Melhorar `data_fim_display` para colorir datas próximas (< 30 dias = vermelho, < 60 = laranja)
5. Converter fieldsets para tabs com `"tab": True`:
   - Partes, Vigência, Financeiro, Rescisão (remover `'classes': ['collapse']`)

### O que NÃO muda
- `GarantiaInline`, `ContratoDocumentoInline`, autocomplete_fields, search_fields — permanecem iguais
- `historico_precos_display` permanece com `format_html` (não é badge, é listagem formatada)

---

## Arquivo 5 — `documentos/admin.py`

### O que muda
1. Adicionar `from unfold.decorators import display` (e `from datetime import date`)
2. Adicionar `from unfold.utils import display_for_label` (consistência com imoveis)
3. Adicionar método `vencimento_badge` com `@display(label={...})`:
   ```python
   @display(description='Vencimento', label={
       'Vencido': 'danger', 'A vencer': 'warning', 'OK': 'success', 'Sem data': 'default',
   })
   def vencimento_badge(self, obj):
       if not obj.vencimento: return 'Sem data'
       diff = (obj.vencimento - date.today()).days
       if diff < 0: return 'Vencido'
       if diff < 30: return 'A vencer'
       return 'OK'
   ```
4. Adicionar `vencimento_badge` em `list_display` (substituindo `vencimento` raw)
5. Adicionar `vencimento_badge` em `readonly_fields`

### O que NÃO muda
- Inlines (`_DocumentoInlineBase` e subclasses) — permanecem iguais
- `DynamicSchemaAdminMixin`, fieldsets, `entidade_display`, `arquivo_link` — permanecem

---

## Arquivo 6 — `imoveis/admin.py`

### O que muda
1. Adicionar `compressed_fields = True`, `warn_unsaved_form = True`, `list_fullwidth = True` em `ImovelAdmin`
2. Adicionar método `status_badge` usando `display_for_label` (já importado):
   ```python
   @admin.display(description='Status')
   def status_badge(self, obj):
       mapa = {
           'AL': ('Alugado',    'success'),
           'DI': ('Disponível', 'info'),
           'RE': ('Reforma',    'warning'),
           'IN': ('Inativo',    'danger'),
           'GT': ('Gest. Terc.','default'),
           'VE': ('À venda',    'default'),
       }
       texto, tipo = mapa.get(obj.status, (obj.status, 'default'))
       return display_for_label(texto, '—', {texto: tipo})
   ```
3. Substituir `'status'` raw por `'status_badge'` em `list_display`
4. Converter fieldsets para tabs com `"tab": True` (Identificação, Endereço, Patrimônio Financeiro)

### O que NÃO muda
- `changelist_view` com totais — permanece igual
- `list_after_template` — permanece (template já existe)
- Inlines, autocomplete_fields, `DynamicSchemaAdminMixin` — permanecem

---

## Itens diferidos para Fase 5

Quando `core` app e `Tarefa` model forem implementados:
- Adicionar `TarefaAdmin` em `core/admin.py` (ver `plano-ux-admin.md` linhas 361-423)
- Atualizar `dashboard_callback` para incluir `tarefas_urgentes`
- Adicionar seção "Operacional / Tarefas" no SIDEBAR
- `'core'` já estará em INSTALLED_APPS (adicionado neste sprint)

---

## Verificação

1. `python manage.py runserver` — abrir admin, confirmar sidebar com grupos e ícones
2. Dashboard (`/admin/`) — verificar cards KPI e gráfico de barras
3. Contratos — verificar badge colorido no status (sem HTML inline no source)
4. Documentos — verificar badge de vencimento na listagem
5. Imóveis — verificar badge de status na listagem; checar totais no rodapé
6. Testar alternância light/dark mode — cores oklch devem funcionar em ambos
