from datetime import date

from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from config.utils import formatar_moeda
from documentos.admin import ContratoDocumentoInline
from .models import Contrato, Garantia


class GarantiaInline(TabularInline):
    model = Garantia
    extra = 0
    tab = True
    fields = ['tipo', 'fiador', 'valor', 'observacoes']
    autocomplete_fields = ['fiador']


@admin.register(Contrato)
class ContratoAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
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
        ('Partes', {'classes': ['tab'], 'fields': ['imovel', 'cliente', 'imobiliaria']}),
        ('Vigência', {'classes': ['tab'], 'fields': [
            'data_inicio', 'vigencia', 'renovacao_automatica', 'quant_renov_automaticas',
            'data_fim_display', 'status_display',
        ]}),
        ('Financeiro', {'classes': ['tab'], 'fields': [
            'valor_aluguel', 'valor_aluguel_display', 'indice_reajuste', 'dia_vencimento',
            'historico_precos_display',
        ]}),
        ('Rescisão', {'classes': ['tab'], 'fields': ['rescindido_em']}),
        ('Observações', {'classes': ['tab'], 'fields': ['observacoes']}),
        ('Auditoria', {'classes': ['tab'], 'fields': ['criado_em', 'atualizado_em']}),
    ]

    @display(description='Status', label={
        'Ativo': 'success', 'Renovado': 'success',
        'Futuro': 'info', 'Vencido': 'danger', 'Rescindido': 'default',
    })
    def status_display(self, obj):
        return obj.status

    @admin.display(description='Término')
    def data_fim_display(self, obj):
        if not obj.data_fim:
            return '—'
        texto = obj.data_fim.strftime('%d/%m/%Y')
        diff = (obj.data_fim - date.today()).days
        if diff < 0:
            return format_html('<span style="color: var(--color-red-500); font-weight: 600">{}</span>', texto)
        if diff < 30:
            return format_html('<span style="color: var(--color-red-400); font-weight: 600">{}</span>', texto)
        if diff < 60:
            return format_html('<span style="color: var(--color-orange-500); font-weight: 600">{}</span>', texto)
        return texto

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
