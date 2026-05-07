# Plano: UX/Admin Unfold — Configuração completa

> **Status:** Fase 4 concluída. Este documento descreve o que foi implementado e o que falta para a Fase 5.

## Context

O Unfold está instalado e configurado com sidebar customizada, dashboard, badges e tabs. O `core` app existe mas ainda não tem o model `Tarefa` (Fase 5).

---

## Estado atual (Fase 4 concluída)

| Arquivo | Status |
|---|---|
| `config/settings.py` | ✅ `UNFOLD` importado de `config/unfold_config.py`; `TEMPLATES DIRS` configurado |
| `config/unfold_config.py` | ✅ Sidebar, cores, environment callback, badge contratos vencendo, `permission_superuser` |
| `core/` app | ✅ Existe — `core/admin.py` registra User/Group com Unfold; `core/views.py` com `dashboard_callback` |
| `templates/admin/index.html` | ✅ Dashboard com KPIs de imóveis e gráfico de barras |
| `contratos/admin.py` | ✅ Badge de status, tabs, `@display` para data_fim e garantia |
| `documentos/admin.py` | ✅ Badge de vencimento, GenericFK interativa (entidade→objeto→tipo), TIPOS_POR_ENTIDADE |
| `imoveis/admin.py` | ✅ Badge de status, tabs, totais no rodapé, campos calculados |
| `pessoas/admin.py` | ✅ Inlines dinâmicos via `get_inlines()`, tabs nos perfis |

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

## Itens pendentes — Fase 5

Quando `Tarefa` model for implementado em `core/models.py`:
- Criar `TarefaAdmin` em `core/admin.py` (ver `plano-ux-admin.md` linhas 361-423)
- Atualizar `dashboard_callback` em `core/views.py` para incluir `tarefas_urgentes`
- Adicionar seção "Operacional / Tarefas" no SIDEBAR em `config/unfold_config.py`
- `'core'` já está em INSTALLED_APPS

---

## Verificação (Fase 4)

1. `python manage.py runserver` — abrir admin, confirmar sidebar com grupos e ícones
2. Dashboard (`/admin/`) — verificar cards KPI e gráfico de barras
3. Contratos — verificar badge colorido no status
4. Documentos — cadastrar documento vinculando a entidade via selects em cascata
5. Imóveis — verificar badge de status na listagem; checar totais no rodapé; editar imóvel e confirmar campos específicos por tipo visíveis
6. Testar alternância light/dark mode — cores oklch devem funcionar em ambos
