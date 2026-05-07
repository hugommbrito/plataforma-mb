from decimal import Decimal

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.utils import display_for_label

from config.dynamic_form import DynamicSchemaAdminMixin, build_conditional_fields, build_meta_field_names
from config.utils import formatar_moeda, formatar_percentual
from documentos.admin import ImovelDocumentoInline
from .forms import ImovelForm
from .models import Imovel, ImovelProprietario

_CONDITIONAL_FIELDS = build_conditional_fields(Imovel.CARACTERISTICAS_SCHEMA)
_META_FIELD_NAMES = build_meta_field_names(Imovel.CARACTERISTICAS_SCHEMA)


class ImovelProprietarioInline(TabularInline):
    model = ImovelProprietario
    extra = 0
    fields = ['proprietario', 'participacao']
    autocomplete_fields = ['proprietario']
    tab = True


@admin.register(Imovel)
class ImovelAdmin(DynamicSchemaAdminMixin, ModelAdmin):
    form = ImovelForm
    conditional_fields = _CONDITIONAL_FIELDS
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_after_template = 'admin/imoveis/imovel/change_list_after.html'
    list_display = ['nome', 'tipo', 'status_badge', 'municipio', 'estado', 'valor_mercado_display', 'valor_por_m2_display', 'participacao_interna_pct_display', 'valor_interno_display', 'registro_regularizado_display']
    list_filter = ['tipo', 'status', 'estado']
    search_fields = ['nome', 'endereco', 'municipio', 'matricula_cartorio']
    autocomplete_fields = ['titular_registro']
    inlines = [ImovelProprietarioInline, ImovelDocumentoInline]
    readonly_fields = ['registro_regularizado_display', 'valor_por_m2_display', 'participacao_interna_pct_display', 'valor_interno_display', 'criado_em', 'atualizado_em']
    fieldsets = [
        ('Identificação', {'classes': ['tab'], 'fields': ['nome', 'tipo', 'status', 'area']}),
        ('Características', {'classes': ['tab'], 'fields': _META_FIELD_NAMES}),
        ('Localização', {'classes': ['tab'], 'fields': ['endereco', 'complemento', 'bairro', 'estado', 'municipio', 'cep']}),
        ('Cartório e Município', {'classes': ['tab'], 'fields': [
            'matricula_cartorio', 'titular_registro', 'registro_regularizado_display',
            'matricula_municipio', 'inscricao_municipal',
        ]}),
        ('Patrimônio Financeiro', {'classes': ['tab'], 'fields': [
            'valor_mercado', 'valor_por_m2_display', 'participacao_interna_pct_display', 'valor_interno_display',
        ]}),
        ('Auditoria', {'classes': ['tab'], 'fields': ['criado_em', 'atualizado_em']}),
        ('Observações', {'fields': ['observacoes']}),
    ]

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs = response.context_data['cl'].queryset.prefetch_related(
                'imovelproprietario_set__proprietario'
            )
            total = sum(
                (i.valor_interno or Decimal('0') for i in qs),
                Decimal('0'),
            )
            response.context_data['total_valor_interno'] = formatar_moeda(total) if total else None
        except (AttributeError, KeyError):
            pass
        return response

    @admin.display(description='Status')
    def status_badge(self, obj):
        mapa = {
            'AL': ('Alugado',     'success'),
            'DI': ('Disponível',  'info'),
            'RE': ('Reforma',     'warning'),
            'IN': ('Inativo',     'danger'),
            'GT': ('Gest. Terc.', 'default'),
            'VE': ('À venda',     'default'),
        }
        texto, tipo = mapa.get(obj.status, (obj.status, 'default'))
        return display_for_label(texto, '—', {texto: tipo})

    @admin.display(description='Valor de Mercado')
    def valor_mercado_display(self, obj):
        return formatar_moeda(obj.valor_mercado)

    @admin.display(description='R$/m²')
    def valor_por_m2_display(self, obj):
        return formatar_moeda(obj.valor_por_m2)

    @admin.display(description='Part. interna')
    def participacao_interna_pct_display(self, obj):
        return formatar_percentual(obj.participacao_interna_pct)

    @admin.display(description='Valor interno (R$)')
    def valor_interno_display(self, obj):
        return formatar_moeda(obj.valor_interno)

    @admin.display(description='Registro')
    def registro_regularizado_display(self, obj):
        status = obj.registro_regularizado
        if status is None:
            return '—'
        texto = 'Regularizado' if status else 'Pendente'
        tipo = 'success' if status else 'danger'
        return display_for_label(texto, '—', {texto: tipo})
