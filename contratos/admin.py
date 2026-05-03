from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from config.utils import formatar_moeda
from documentos.admin import ContratoDocumentoInline
from .models import Contrato, Garantia


class GarantiaInline(TabularInline):
    model = Garantia
    extra = 1
    fields = ['tipo', 'fiador', 'valor', 'observacoes']
    autocomplete_fields = ['fiador']


@admin.register(Contrato)
class ContratoAdmin(ModelAdmin):
    list_display = [
        'imovel', 'cliente', 'status_display', 'data_inicio', 'data_fim_display',
        'valor_aluguel_display', 'indice_reajuste',
    ]
    list_filter = ['indice_reajuste', 'renovacao_automatica', 'imovel__estado']
    search_fields = ['imovel__nome', 'cliente__pessoa__nome', 'cliente__pessoa__apelido']
    autocomplete_fields = ['imovel', 'cliente', 'imobiliaria']
    inlines = [GarantiaInline, ContratoDocumentoInline]
    readonly_fields = [
        'status_display', 'data_fim_display', 'valor_aluguel_display',
        'historico_precos_display', 'criado_em', 'atualizado_em',
    ]
    fieldsets = [
        ('Partes', {'fields': ['imovel', 'cliente', 'imobiliaria']}),
        ('Vigência', {'fields': [
            'data_inicio', 'vigencia', 'renovacao_automatica', 'quant_renov_automaticas',
            'data_fim_display', 'status_display',
        ]}),
        ('Financeiro', {'fields': [
            'valor_aluguel', 'valor_aluguel_display', 'indice_reajuste', 'dia_vencimento',
            'historico_precos_display',
        ]}),
        ('Rescisão', {'fields': ['rescindido_em'], 'classes': ['collapse']}),
        ('Observações', {'fields': ['observacoes'], 'classes': ['collapse']}),
        ('Auditoria', {'fields': ['criado_em', 'atualizado_em'], 'classes': ['collapse']}),
    ]

    @admin.display(description='Status')
    def status_display(self, obj):
        cores = {
            'Ativo':      'green',
            'Renovado':   'blue',
            'Futuro':     'gray',
            'Vencido':    'red',
            'Rescindido': 'orange',
        }
        cor = cores.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: 600">{}</span>', cor, obj.status
        )

    @admin.display(description='Término')
    def data_fim_display(self, obj):
        return obj.data_fim.strftime('%d/%m/%Y') if obj.data_fim else '—'

    @admin.display(description='Aluguel atual')
    def valor_aluguel_display(self, obj):
        return formatar_moeda(obj.valor_aluguel)

    @admin.display(description='Histórico de valores')
    def historico_precos_display(self, obj):
        periodos = obj.historico_precos
        if not periodos:
            return '—'
        linhas = []
        for p in periodos:
            fim = p['fim'].strftime('%d/%m/%Y') if p['fim'] else 'atual'
            linhas.append(
                f"{formatar_moeda(p['valor'])} &nbsp; "
                f"<span style='color:#6b7280'>{p['inicio'].strftime('%d/%m/%Y')} → {fim}</span>"
            )
        return format_html('<br>'.join(linhas))
