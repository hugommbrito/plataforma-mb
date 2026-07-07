import json
from django.db.models import Count
from imoveis.models import Imovel
from pessoas.models import PerfilProprietario
from config.utils import formatar_moeda
from config.unfold_config import UNFOLD

_STATUS_LABELS = dict(Imovel.Status.choices)
_PRIMARY_COLOR = UNFOLD["COLORS"]["primary"]["500"]

_STATUS_COLORS = {
    "AL": "oklch(62% 0.17 145)",   # verde — Alugado
    "DI": "oklch(62% 0.17 250)",   # azul  — Disponível
    "RE": "oklch(72% 0.18  75)",   # âmbar — Reforma
    "IN": "oklch(57% 0.20  25)",   # vermelho — Inativo
    "GT": "oklch(60% 0.05 250)",   # cinza-azulado — Gest. Terc.
    "VE": "oklch(60% 0.05 250)",   # cinza-azulado — À venda
    "VD": "oklch(45% 0.05 250)",   # cinza-azulado-escuro — Vendido
}


def dashboard_callback(request, context):
    imoveis = Imovel.objects.all()

    total = imoveis.count()
    alugados = imoveis.filter(status="AL").count()
    estados = imoveis.exclude(estado="").values("estado").distinct().count()
    ocupacao = round(alugados / total * 100) if total else 0
    prop_internos = PerfilProprietario.objects.filter(
        interno=True,
        imovelproprietario__isnull=False,
    ).distinct().count()

    context.update({
        "total_imoveis": total,
        "imoveis_alugados": alugados,
        "valor_interno_total": formatar_moeda(
            sum(i.valor_interno for i in imoveis if i.valor_interno) or None
        ),
        "kpi_imoveis_sub": f"{estados} estado{'s' if estados != 1 else ''}",
        "kpi_alugados_sub": f"{ocupacao}% ocupação",
        "kpi_valor_sub": f"{prop_internos} proprietário{'s' if prop_internos != 1 else ''} interno{'s' if prop_internos != 1 else ''}",
    })

    status_data = (
        imoveis
        .values("status")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    context["chart_status"] = json.dumps({
        "labels": [_STATUS_LABELS.get(s["status"], s["status"]) for s in status_data],
        "datasets": [{
            "data": [s["total"] for s in status_data],
            "backgroundColor": [_STATUS_COLORS.get(s["status"], _PRIMARY_COLOR) for s in status_data],
            "borderWidth": 0,
        }],
    })

    estado_data = (
        imoveis
        .exclude(estado="")
        .values("estado")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    context["chart_estado"] = json.dumps({
        "labels": [e["estado"] for e in estado_data],
        "datasets": [{
            "data": [e["total"] for e in estado_data],
            "backgroundColor": _PRIMARY_COLOR,
            "borderRadius": 4,
        }],
    })

    return context
