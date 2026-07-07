# Plano de Implementação — UX/Admin Plataforma MB

> Gerado a partir da análise de design em `Sugestoes Plataforma MB.html`.  
> Todas as sugestões usam **exclusivamente** componentes nativos do `django-unfold`.  
> Nenhuma dependência nova é necessária. Nenhuma migration é necessária.

---

## Contexto

- Stack: Django + django-unfold + Neon Postgres + Cloudflare R2 + Railway
- Fases 0–3 concluídas (Pessoas, Imóveis, Contratos, Garantias)
- Fases 4–6 em andamento (Documentos, Lembretes, Relatórios)
- O responsável opera remotamente de Toronto — o sistema precisa ser autônomo e informativo

---

## Prioridade 1 — Implementar imediatamente (sem migrations, ~1 tarde)

### 1. Sidebar com navegação real

**Arquivo:** `config/settings.py`

Substituir a navegação automática do Unfold por uma configuração explícita com ícones Material Symbols, grupos semânticos e badges dinâmicos.

```python
# config/settings.py
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

def badge_contratos_vencendo(request):
    """Retorna contagem de contratos vencendo em 60 dias. None oculta o badge."""
    from contratos.models import Contrato
    from datetime import date, timedelta
    alvo = date.today() + timedelta(days=60)
    count = sum(
        1 for c in Contrato.objects.filter(rescindido_em__isnull=True)
        if c.data_fim and c.data_fim <= alvo
    )
    return count or None

def environment_callback(request):
    """Badge vermelho em produção, azul em desenvolvimento."""
    import os
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        return ["Produção", "danger"]
    return ["Local", "info"]

UNFOLD = {
    "SITE_TITLE": "Plataforma MB",
    "SITE_HEADER": "Plataforma MB",
    "SITE_SYMBOL": "home_work",
    "ENVIRONMENT": "config.settings.environment_callback",
    "DASHBOARD_CALLBACK": "core.views.dashboard_callback",
    "BORDER_RADIUS": "8px",
    "COLORS": {
        "primary": {
            "50":  "oklch(97.7% 0.013 250)",
            "100": "oklch(94.2% 0.032 250)",
            "200": "oklch(88.5% 0.065 250)",
            "300": "oklch(80.0% 0.110 250)",
            "400": "oklch(68.5% 0.155 250)",
            "500": "oklch(56.0% 0.175 250)",
            "600": "oklch(48.0% 0.160 250)",
            "700": "oklch(40.0% 0.140 250)",
            "800": "oklch(30.0% 0.110 250)",
            "900": "oklch(22.0% 0.080 250)",
            "950": "oklch(14.0% 0.055 250)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "command_search": True,  # ativa ⌘K
        "navigation": [
            {
                "title": _("Visão Geral"),
                "separator": True,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Patrimônio"),
                "items": [
                    {
                        "title": _("Imóveis"),
                        "icon": "home_work",
                        "link": reverse_lazy("admin:imoveis_imovel_changelist"),
                    },
                    {
                        "title": _("Contratos"),
                        "icon": "description",
                        "link": reverse_lazy("admin:contratos_contrato_changelist"),
                        "badge": "config.settings.badge_contratos_vencendo",
                    },
                    {
                        "title": _("Documentos"),
                        "icon": "folder",
                        "link": reverse_lazy("admin:documentos_documento_changelist"),
                    },
                ],
            },
            {
                "title": _("Pessoas"),
                "items": [
                    {
                        "title": _("Todas as pessoas"),
                        "icon": "group",
                        "link": reverse_lazy("admin:pessoas_pessoa_changelist"),
                    },
                    {
                        "title": _("Inquilinos"),
                        "icon": "vpn_key",
                        "link": reverse_lazy("admin:pessoas_perfilcliente_changelist"),
                    },
                    {
                        "title": _("Proprietários"),
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:pessoas_perfilproprietario_changelist"),
                    },
                    {
                        "title": _("Imobiliárias"),
                        "icon": "business",
                        "link": reverse_lazy("admin:pessoas_perfilimobiliaria_changelist"),
                    },
                    {
                        "title": _("Fiadores"),
                        "icon": "shield_person",
                        "link": reverse_lazy("admin:pessoas_perfilfiad_changelist"),
                    },
                ],
            },
            {
                "title": _("Operacional"),
                "items": [
                    {
                        "title": _("Tarefas"),
                        "icon": "task_alt",
                        "link": reverse_lazy("admin:core_tarefa_changelist"),
                    },
                ],
            },
        ],
    },
}
```

> ⚠️ Ajustar os nomes de app/model nos `reverse_lazy` conforme o `app_label` real de cada model.

---

### 2. Dashboard com KPIs — DASHBOARD_CALLBACK

**Arquivo:** `core/views.py` (criar se não existir)  
**Template:** `templates/admin/index.html` (criar)

```python
# core/views.py
import json
from datetime import date, timedelta
from django.db.models import Count
from imoveis.models import Imovel
from core.models import Tarefa


def dashboard_callback(request, context):
    hoje = date.today()
    imoveis = Imovel.objects.all()

    # KPIs
    context.update({
        "total_imoveis":    imoveis.count(),
        "imoveis_alugados": imoveis.filter(status="AL").count(),
        "valor_interno_total": sum(
            i.valor_interno for i in imoveis if i.valor_interno
        ),
        "tarefas_urgentes": Tarefa.objects.filter(
            concluida=False,
            vencimento__lte=hoje + timedelta(days=7),
        ).order_by("vencimento")[:5],
        "total_tarefas_abertas": Tarefa.objects.filter(concluida=False).count(),
    })

    # Dados para gráfico de barras por status
    status_data = (
        imoveis
        .values("status")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    context["chart_status"] = json.dumps({
        "labels": [s["status"] for s in status_data],
        "datasets": [{
            "data":            [s["total"] for s in status_data],
            "backgroundColor": "oklch(56% 0.16 250 / 0.7)",
            "borderRadius":    4,
        }],
    })

    return context
```

```django
{# templates/admin/index.html #}
{% extends 'admin/base.html' %}
{% load i18n unfold %}

{% block content %}

{# ── Linha de KPIs ── #}
{% component "unfold/components/flex.html" with class="gap-6 mb-8" %}
  {% component "unfold/components/card.html" with class="lg:w-1/4" %}
    {% component "unfold/components/text.html" %}{% trans "Total de Imóveis" %}{% endcomponent %}
    {% component "unfold/components/title.html" %}{{ total_imoveis }}{% endcomponent %}
  {% endcomponent %}

  {% component "unfold/components/card.html" with class="lg:w-1/4" %}
    {% component "unfold/components/text.html" %}{% trans "Alugados" %}{% endcomponent %}
    {% component "unfold/components/title.html" %}{{ imoveis_alugados }}{% endcomponent %}
  {% endcomponent %}

  {% component "unfold/components/card.html" with class="lg:w-1/4" %}
    {% component "unfold/components/text.html" %}{% trans "Valor Interno (holding)" %}{% endcomponent %}
    {% component "unfold/components/title.html" %}{{ valor_interno_total|floatformat:0 }}{% endcomponent %}
  {% endcomponent %}

  {% component "unfold/components/card.html" with class="lg:w-1/4" %}
    {% component "unfold/components/text.html" %}{% trans "Tarefas abertas" %}{% endcomponent %}
    {% component "unfold/components/title.html" %}{{ total_tarefas_abertas }}{% endcomponent %}
  {% endcomponent %}
{% endcomponent %}

{# ── Gráfico por status ── #}
{% trans "Imóveis por situação" as chart_title %}
{% component "unfold/components/card.html" with title=chart_title class="mb-8" %}
  {% component "unfold/components/chart/bar.html" with data=chart_status height=280 %}{% endcomponent %}
{% endcomponent %}

{# ── Tarefas urgentes ── #}
{% if tarefas_urgentes %}
{% trans "Tarefas urgentes (próximos 7 dias)" as tasks_title %}
{% component "unfold/components/card.html" with title=tasks_title %}
  {% component "unfold/components/flex.html" with class="flex-col gap-2" %}
    {% for tarefa in tarefas_urgentes %}
      {% component "unfold/components/text.html" %}
        {{ tarefa.titulo }} — vence em {{ tarefa.vencimento }}
      {% endcomponent %}
    {% endfor %}
  {% endcomponent %}
{% endcomponent %}
{% endif %}

{% endblock %}
```

---

### 3. ContratoAdmin — expor properties existentes

**Arquivo:** `contratos/admin.py`

```python
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from datetime import date
from unfold.admin import ModelAdmin
from unfold.decorators import display, action
from .models import Contrato, Garantia


class GarantiaInline(admin.TabularInline):
    model = Garantia
    extra = 0


@admin.register(Contrato)
class ContratoAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth    = True

    list_display = [
        "imovel",
        "cliente",
        "get_status_badge",
        "get_valor",
        "get_data_fim",
        "get_garantia_tipo",
    ]
    list_filter   = ["indice_reajuste", "renovacao_automatica"]
    search_fields = [
        "imovel__nome",
        "cliente__pessoa__nome",
        "cliente__pessoa__cpf_cnpj",
    ]
    inlines = [GarantiaInline]

    fieldsets = (
        (_("Dados do Contrato"), {
            "tab": True,
            "fields": [
                "imovel", "cliente", "imobiliaria",
                "data_inicio", "vigencia",
                "renovacao_automatica", "quant_renov_automaticas",
                "dia_vencimento",
            ],
        }),
        (_("Financeiro"), {
            "tab": True,
            "fields": ["valor_aluguel", "indice_reajuste"],
        }),
        (_("Rescisão"), {
            "tab": True,
            "fields": ["rescindido_em"],
        }),
    )

    @display(description=_("Status"), label={
        "Ativo":      "success",
        "Vencendo":   "warning",
        "Vencido":    "danger",
        "Futuro":     "info",
        "Renovado":   "success",
        "Rescindido": "default",
    })
    def get_status_badge(self, obj):
        # @property já implementada no model
        return obj.status

    @display(description=_("Valor"), ordering="valor_aluguel")
    def get_valor(self, obj):
        from config.utils import formatar_moeda
        return formatar_moeda(obj.valor_aluguel)

    @display(description=_("Vencimento"), ordering="data_inicio")
    def get_data_fim(self, obj):
        if not obj.data_fim:
            return "—"
        diff = (obj.data_fim - date.today()).days
        txt  = obj.data_fim.strftime("%d/%m/%Y")
        cor  = "#dc2626" if diff < 30 else ("#d97706" if diff < 60 else "inherit")
        return format_html('<span style="color:{};font-weight:500">{}</span>', cor, txt)

    @display(description=_("Garantia"))
    def get_garantia_tipo(self, obj):
        g = obj.garantia_set.first()
        return g.get_tipo_display() if g else "—"
```

---

### 4. TarefaAdmin — central operacional

**Arquivo:** `core/admin.py`

```python
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta
from unfold.admin import ModelAdmin
from unfold.decorators import display, action
from .models import Tarefa


@admin.register(Tarefa)
class TarefaAdmin(ModelAdmin):
    list_fullwidth    = True
    compressed_fields = True

    list_display = [
        "titulo",
        "tipo",
        "get_vencimento",
        "recorrencia",
        "get_entidade",
        "get_status_badge",
    ]
    list_filter = ["concluida", "tipo", "recorrencia"]
    actions     = ["marcar_concluidas"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Padrão: mostrar apenas não concluídas
        if not request.GET.get("concluida__exact"):
            return qs.filter(concluida=False)
        return qs

    @display(description=_("Status"), label={
        "Urgente":  "danger",
        "Pendente": "warning",
        "Concluída":"success",
    })
    def get_status_badge(self, obj):
        if obj.concluida:
            return "Concluída"
        if obj.vencimento and obj.vencimento <= date.today() + timedelta(days=7):
            return "Urgente"
        return "Pendente"

    @display(description=_("Vencimento"), ordering="vencimento")
    def get_vencimento(self, obj):
        if not obj.vencimento:
            return "—"
        from django.utils.html import format_html
        diff = (obj.vencimento - date.today()).days
        cor  = "#dc2626" if diff <= 3 else ("#d97706" if diff <= 7 else "inherit")
        return format_html(
            '<span style="color:{}">{}</span>',
            cor, obj.vencimento.strftime("%d/%m/%Y")
        )

    @display(description=_("Entidade vinculada"))
    def get_entidade(self, obj):
        return str(obj.content_object) if obj.content_object else "—"

    @action(description=_("Marcar selecionadas como concluídas"))
    def marcar_concluidas(self, request, queryset):
        queryset.update(concluida=True)
```

---

## Prioridade 2 — Sprint seguinte (junto com Fase 5)

### 5. ImovelAdmin — expor propriedades calculadas

**Arquivo:** `imoveis/admin.py`

```python
from unfold.contrib.filters.admin import DropdownFilter
from unfold.decorators import display
from config.utils import formatar_moeda  # já existe


@admin.register(Imovel)
class ImovelAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth    = True

    list_display = [
        "nome",
        "cidade",
        "get_status_badge",
        "get_area",
        "get_valor_mercado",
        "get_valor_m2",
        "get_participacao_interna",
    ]
    list_filter = [
        ("cidade", DropdownFilter),
        ("estado", DropdownFilter),
        ("status", DropdownFilter),
        ("tipo",   DropdownFilter),
    ]
    readonly_fields = [
        "valor_por_m2",
        "participacao_interna_pct",
        "valor_interno",
    ]
    # Tabs para organizar o formulário
    fieldsets = (
        (_("Identificação"), {
            "tab": True,
            "fields": ["nome", "tipo", "status", "matricula", "area_total", "quartos", "vagas", "valor_mercado"],
        }),
        (_("Endereço"), {
            "tab": True,
            "fields": ["endereco", "complemento", "bairro", "cidade", "estado", "cep"],
        }),
        (_("Calculados"), {
            "tab": True,
            "fields": ["valor_por_m2", "participacao_interna_pct", "valor_interno"],
        }),
    )

    @display(description=_("Status"), label={
        "AL": "success",
        "DI": "info",
        "RE": "warning",
        "IN": "danger",
        "GT": "default",
        "VE": "default",
    })
    def get_status_badge(self, obj):
        return obj.status

    @display(description=_("Área"), ordering="area_total")
    def get_area(self, obj):
        return f"{obj.area_total} m²" if obj.area_total else "—"

    @display(description=_("Valor de mercado"), ordering="valor_mercado")
    def get_valor_mercado(self, obj):
        return formatar_moeda(obj.valor_mercado)

    @display(description=_("R$/m²"))
    def get_valor_m2(self, obj):
        return formatar_moeda(obj.valor_por_m2)  # @property existente

    @display(description=_("Part. interna"))
    def get_participacao_interna(self, obj):
        pct = obj.participacao_interna_pct  # @property existente
        return f"{pct:.0%}" if pct else "—"
```

**Totais no rodapé da lista** (já documentado no CLAUDE.md como padrão existente):

```python
# Adicionar em ImovelAdmin:
list_after_template = "imoveis/admin/changelist_totals.html"

def changelist_view(self, request, extra_context=None):
    extra_context = extra_context or {}
    qs = self.get_queryset(request)
    extra_context["total_valor_mercado"] = sum(
        i.valor_mercado for i in qs if i.valor_mercado
    )
    extra_context["total_valor_interno"] = sum(
        i.valor_interno for i in qs if i.valor_interno
    )
    return super().changelist_view(request, extra_context=extra_context)
```

```django
{# imoveis/templates/imoveis/admin/changelist_totals.html #}
<div style="padding: 12px 16px; font-size: 13px; color: var(--unfold-text-muted);">
  Total: <strong>{{ total_valor_mercado|floatformat:0 }}</strong> valor de mercado ·
  <strong>{{ total_valor_interno|floatformat:0 }}</strong> valor interno da holding
</div>
```

---

### 6. DocumentoAdmin — alertas de vencimento (Fase 4)

**Arquivo:** `documentos/admin.py` — criar junto com o model na Fase 4

```python
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import DropdownFilter
from unfold.decorators import display
from django.utils.html import format_html
from datetime import date


@admin.register(Documento)
class DocumentoAdmin(ModelAdmin):
    list_fullwidth    = True
    compressed_fields = True

    list_display  = ["tipo", "get_entidade", "get_vencimento_badge", "get_download"]
    list_filter   = [("tipo", DropdownFilter)]
    search_fields = ["tipo"]

    @display(description=_("Entidade"))
    def get_entidade(self, obj):
        return str(obj.content_object) if obj.content_object else "—"

    @display(description=_("Vencimento"), label={
        "Vencido":  "danger",
        "A vencer": "warning",
        "OK":       "success",
        "Sem data": "default",
    })
    def get_vencimento_badge(self, obj):
        if not obj.vencimento:
            return "Sem data"
        diff = (obj.vencimento - date.today()).days
        if diff < 0:   return "Vencido"
        if diff < 30:  return "A vencer"
        return "OK"

    @display(description=_("Arquivo"))
    def get_download(self, obj):
        if not obj.arquivo:
            return "—"
        # URL assinada automática via S3Boto3Storage (R2)
        return format_html('<a href="{}" target="_blank">↓ Baixar</a>', obj.arquivo.url)
```

**Inline para usar em outros admins:**

```python
# Adicionar em ImovelAdmin, ContratoAdmin, PessoaAdmin:
from documentos.admin import DocumentoInline  # criar com GenericTabularInline

class DocumentoInline(GenericTabularInline):
    model = Documento
    extra = 0
    fields = ["tipo", "arquivo", "vencimento"]
```

---

## Prioridade 3 — Pós-MVP

### Actions para Fase 6 (Relatórios)

```python
# contratos/admin.py — adicionar em ContratoAdmin
@action(description=_("Exportar rendimentos para IR (CSV)"), icon="download")
def exportar_relatorio_ir(self, request, queryset):
    """REL-02: rendimentos anuais por CPF de proprietário."""
    # implementar geração CSV
    pass

# imoveis/admin.py — adicionar em ImovelAdmin
@action(description=_("Relatório patrimonial consolidado"), icon="summarize")
def relatorio_patrimonial(self, request, queryset):
    """REL-01: relatório consolidado com imóveis, valores e participações."""
    pass
```

---

## Checklist de implementação

### Fase 4 — concluída ✅
- [x] Atualizar `UNFOLD` em `settings.py` com sidebar, cores e environment callback
- [x] Criar `core/views.py` com `dashboard_callback`
- [x] Criar `templates/admin/index.html` com KPIs e gráfico
- [x] Atualizar `contratos/admin.py` com `@display` para status, data_fim e garantia
- [x] Registrar `User` e `Group` com `ModelAdmin` do Unfold em `core/admin.py`
- [x] Criar `documentos/admin.py` com alerts de vencimento e GenericFK interativa
- [x] Adicionar `DocumentoInline` em Imovel, Contrato, Pessoa e todos os Perfil*
- [x] Atualizar `imoveis/admin.py` com badges, tabs e totais patrimoniais
- [x] `pessoas/admin.py` — inlines dinâmicos via `get_inlines()` (só mostra perfis que existem)
- [x] Renomear `cidade` → `municipio` em Imovel (model, form, admin, widget, JS, migration)

### Fase 5 — próxima
- [ ] Model `Tarefa` em `core/models.py` com GenericFK
- [ ] `TarefaAdmin` em `core/admin.py` com badges de urgência e action de conclusão (ver plano-ux-admin.md linhas 361-423)
- [ ] Atualizar `dashboard_callback` em `core/views.py` para incluir `tarefas_urgentes`
- [ ] Adicionar seção "Operacional / Tarefas" no SIDEBAR em `config/unfold_config.py`
- [ ] 6 management commands + Railway crons
- [ ] E-mail SMTP simples

### Fase 6 / Pós-MVP
- [ ] Custom action: `exportar_relatorio_ir` em ContratoAdmin (REL-02)
- [ ] Custom action: `relatorio_patrimonial` em ImovelAdmin (REL-01)
- [ ] Custom action: `calcular_reajuste` via API BACEN em ContratoAdmin (CON-02)
- [ ] Custom action: `gerar_recibo_pdf` via reportlab em ContratoAdmin (CON-06)

---

## Referências

- [django-unfold components](https://unfoldadmin.com/docs/components/introduction/)
- [dashboard customization](https://unfoldadmin.com/docs/configuration/dashboard/)
- [sidebar navigation](https://unfoldadmin.com/docs/configuration/sidebar-navigation/)
- [ModelAdmin options](https://unfoldadmin.com/docs/configuration/modeladmin/)
- [unfold decorators (@display, @action)](https://unfoldadmin.com/docs/actions/overview/)
