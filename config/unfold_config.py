from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


def badge_contratos_vencendo(request):
    from contratos.models import Contrato
    from datetime import date, timedelta
    alvo = date.today() + timedelta(days=60)
    count = sum(
        1 for c in Contrato.objects.filter(rescindido_em__isnull=True)
        if c.data_fim and c.data_fim <= alvo
    )
    return count or None


def environment_callback(request):
    import os
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        return ["Produção", "danger"]
    return ["Local", "info"]


UNFOLD = {
    "SITE_TITLE": "Plataforma MB",
    "SITE_HEADER": "Plataforma MB",
    "SITE_SYMBOL": "home_work",
    "ENVIRONMENT": "config.unfold_config.environment_callback",
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
                        "badge": "config.unfold_config.badge_contratos_vencendo",
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
                        "link": reverse_lazy("admin:pessoas_perfilfiador_changelist"),
                    },
                ],
            },
        ],
    },
}
