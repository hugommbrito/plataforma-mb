from decimal import Decimal

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from config.dynamic_form import DynamicSchemaAdminMixin, build_conditional_fields, build_meta_field_names
from config.utils import formatar_moeda, formatar_percentual
from documentos.admin import ImovelDocumentoInline
from .forms import ImovelForm
from .models import Imovel, ImovelProprietario

_CONDITIONAL_FIELDS = build_conditional_fields(Imovel.CARACTERISTICAS_SCHEMA)
_META_FIELD_NAMES = build_meta_field_names(Imovel.CARACTERISTICAS_SCHEMA)


class ImovelProprietarioInline(TabularInline):
    model = ImovelProprietario
    extra = 1
    fields = ['proprietario', 'participacao']
    autocomplete_fields = ['proprietario']


@admin.register(Imovel)
class ImovelAdmin(DynamicSchemaAdminMixin, ModelAdmin):
    form = ImovelForm
    conditional_fields = _CONDITIONAL_FIELDS
    list_after_template = 'admin/imoveis/imovel/change_list_after.html'
    list_display =['nome', 'tipo', 'status', 'cidade', 'estado', 'valor_mercado_display', 'valor_por_m2_display', 'participacao_interna_pct_display', 'valor_interno_display']
    list_filter = ['tipo', 'status', 'estado']
    search_fields = ['nome', 'endereco', 'cidade', 'matricula']
    inlines = [ImovelProprietarioInline, ImovelDocumentoInline]
    readonly_fields = ['valor_por_m2_display', 'participacao_interna_pct_display', 'valor_interno_display', 'criado_em', 'atualizado_em']
    fieldsets = [
        ('Identificação', {'fields': ['nome', 'tipo', 'status', 'matricula']}),
        ('Características', {'fields': ['area_total']}),
        ('Características específicas', {'fields': _META_FIELD_NAMES}),
        ('Localização', {'fields': ['endereco', 'complemento', 'bairro', 'estado', 'cidade', 'cep']}),
        ('Patrimônio Financeiro', {'fields': ['valor_mercado', 'valor_por_m2_display', 'participacao_interna_pct_display', 'valor_interno_display']}),
        ('Observações', {'fields': ['observacoes'], 'classes': ['collapse']}),
        ('Auditoria', {'fields': ['criado_em', 'atualizado_em'], 'classes': ['collapse']}),
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
