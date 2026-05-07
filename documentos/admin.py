from datetime import date

from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import GenericTabularInline, ModelAdmin
from unfold.decorators import display
from unfold.utils import display_for_label

from config.dynamic_form import DynamicSchemaAdminMixin, build_conditional_fields, build_meta_field_names
from .forms import DocumentoForm
from .models import Documento

T = Documento.Tipo

_CONDITIONAL_FIELDS = build_conditional_fields(Documento.METADADOS_SCHEMA)
_META_FIELD_NAMES = build_meta_field_names(Documento.METADADOS_SCHEMA)

# Fonte única dos tipos permitidos por entidade.
# Chave = ContentType.model (model_name em minúsculas), valor = lista de Tipo.
TIPOS_POR_ENTIDADE = {
    'imovel':             [T.MATRICULA, T.ESCRITURA, T.IPTU, T.LICENCA, T.CND_MUNICIPAL, T.FICHA_CADASTRAL, T.CERTIDAO_REGISTRO, T.CERTIDAO_INT_TEOR, T.ESCRITURA_PUBLICA, T.OUTRO],
    'contrato':           [T.CONTRATO, T.ADITIVO, T.COMPROVANTE, T.SEGURO, T.OUTRO],
    'pessoa':             [T.IDENTIDADE, T.COMPROVANTE_RENDA, T.PROCURACAO, T.OUTRO],
    'perfilproprietario': [T.IDENTIDADE, T.PROCURACAO, T.OUTRO],
    'perfilcliente':      [T.IDENTIDADE, T.COMPROVANTE_RENDA, T.CONSULTA_CREDITO, T.OUTRO],
    'perfilimobiliaria':  [T.IDENTIDADE, T.PROCURACAO, T.LICENCA, T.OUTRO],
    'perfilfiador':       [T.IDENTIDADE, T.COMPROVANTE_RENDA, T.CONSULTA_CREDITO, T.OUTRO],
}


class _DocumentoInlineBase(GenericTabularInline):
    model = Documento
    extra = 0
    tab = True
    fields = ['tipo', 'arquivo', 'descricao', 'vencimento']
    show_full_result_count = False
    tipos_permitidos = None

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if self.tipos_permitidos:
            campo = formset.form.base_fields['tipo']
            campo.choices = [(v, l) for v, l in T.choices if v in self.tipos_permitidos]
        return formset


class ImovelDocumentoInline(_DocumentoInlineBase):
    tipos_permitidos = TIPOS_POR_ENTIDADE['imovel']


class ContratoDocumentoInline(_DocumentoInlineBase):
    tipos_permitidos = TIPOS_POR_ENTIDADE['contrato']


class PessoaDocumentoInline(_DocumentoInlineBase):
    tipos_permitidos = TIPOS_POR_ENTIDADE['pessoa']


class PerfilProprietarioDocumentoInline(_DocumentoInlineBase):
    tipos_permitidos = TIPOS_POR_ENTIDADE['perfilproprietario']


class PerfilClienteDocumentoInline(_DocumentoInlineBase):
    tipos_permitidos = TIPOS_POR_ENTIDADE['perfilcliente']


class PerfilImobiliariaDocumentoInline(_DocumentoInlineBase):
    tipos_permitidos = TIPOS_POR_ENTIDADE['perfilimobiliaria']


class PerfilFiadorDocumentoInline(_DocumentoInlineBase):
    tipos_permitidos = TIPOS_POR_ENTIDADE['perfilfiador']


@admin.register(Documento)
class DocumentoAdmin(DynamicSchemaAdminMixin, ModelAdmin):
    form = DocumentoForm
    conditional_fields = _CONDITIONAL_FIELDS
    _extra_form_fields = ['entidade', 'objeto']
    list_display = ['tipo', 'descricao', 'entidade_display', 'vencimento_badge', 'arquivo_link', 'criado_em']
    list_filter = ['tipo']
    search_fields = ['descricao', 'arquivo']
    readonly_fields = ['entidade_display', 'arquivo_link', 'vencimento_badge', 'criado_em']
    fieldsets = [
        ('Arquivo', {'fields': ['arquivo', 'arquivo_link', 'descricao']}),
        ('Vínculo', {'fields': ['entidade', 'objeto', 'tipo']}),
        ('Campos específicos', {'fields': _META_FIELD_NAMES}),
        ('Prazo', {'fields': ['vencimento', 'vencimento_badge']}),
        ('Auditoria', {'fields': ['criado_em'], 'classes': ['collapse']}),
    ]

    class Media:
        js = ('documentos/js/documento_form.js',)

    @admin.display(description='Vinculado a')
    def entidade_display(self, obj):
        if obj.content_object:
            return f'{obj.content_object.__class__.__name__}: {obj.content_object}'
        return '—'

    @admin.display(description='Arquivo')
    def arquivo_link(self, obj):
        if obj.arquivo:
            return format_html('<a href="{}" target="_blank">Baixar</a>', obj.arquivo.url)
        return '—'

    @display(description='Situação', label={
        'Vencido': 'danger', 'A vencer': 'warning', 'OK': 'success', 'Sem data': 'default',
    })
    def vencimento_badge(self, obj):
        if not obj.vencimento:
            return 'Sem data'
        diff = (obj.vencimento - date.today()).days
        if diff < 0:
            return 'Vencido'
        if diff < 30:
            return 'A vencer'
        return 'OK'
