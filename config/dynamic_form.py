"""
Utilitários para formulários com campos dinâmicos baseados em um schema JSON.

Padrão de uso:
    - Declare um schema na model como um dict: {chave_discriminadora: [campo_descritores]}
    - Cada campo_descritor: {'campo': str, 'label': str, 'tipo': texto|numero|decimal|data|booleano, 'obrigatorio': bool}
    - Use DynamicSchemaFormMixin no ModelForm para expor os campos dinamicamente
    - Use DynamicSchemaAdminMixin no ModelAdmin para contornar a validação do modelform_factory
    - Use build_conditional_fields() no ModelAdmin para ocultar/mostrar via Alpine.js (Unfold)

Exemplo (documentos):
    class DocumentoForm(DynamicSchemaFormMixin, forms.ModelForm):
        schema = Documento.METADADOS_SCHEMA
        class Meta:
            model = Documento
            exclude = ['metadados']

    @admin.register(Documento)
    class DocumentoAdmin(DynamicSchemaAdminMixin, ModelAdmin):
        form = DocumentoForm
        conditional_fields = build_conditional_fields(Documento.METADADOS_SCHEMA)
        fieldsets = [..., ('Campos específicos', {'fields': build_meta_field_names(Documento.METADADOS_SCHEMA)})]
"""

import json
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.admin.utils import flatten_fieldsets
from unfold.widgets import (
    UnfoldAdminDecimalFieldWidget,
    UnfoldAdminIntegerFieldWidget,
    UnfoldAdminSingleDateWidget,
    UnfoldAdminTextInputWidget,
    UnfoldAdminNullBooleanSelectWidget
)


def build_meta_info(schema):
    """Retorna dict ordenado campo → primeiro descritor que o define (determina o tipo do campo)."""
    seen = {}
    for campos in schema.values():
        for c in campos:
            if c['campo'] not in seen:
                seen[c['campo']] = c
    return seen


def _build_campo_to_tipos(schema):
    mapping = defaultdict(list)
    for tipo_key, campos in schema.items():
        for c in campos:
            mapping[c['campo']].append(tipo_key)
    return dict(mapping)


def build_conditional_fields(schema, prefix='meta_', discriminator='tipo'):
    """
    Gera o dict `conditional_fields` do Unfold ModelAdmin.
    Cada valor é uma expressão Alpine.js: `['MA','ES'].includes(tipo)`.
    """
    campo_to_tipos = _build_campo_to_tipos(schema)
    return {
        f'{prefix}{campo}': f"{json.dumps(tipos)}.includes({discriminator})"
        for campo, tipos in campo_to_tipos.items()
    }


def build_meta_field_names(schema, prefix='meta_'):
    """Retorna a lista de nomes de campos dinâmicos na ordem de declaração do schema."""
    return [f'{prefix}{campo}' for campo in build_meta_info(schema)]


def make_schema_form_field(info):
    """Cria um campo de formulário Django a partir de um descritor do schema."""
    label = info['label']
    kwargs = {'label': label, 'required': False}
    tipo = info['tipo']
    if tipo == 'texto':
        return forms.CharField(**kwargs, widget=UnfoldAdminTextInputWidget())
    if tipo == 'numero':
        return forms.IntegerField(**kwargs, widget=UnfoldAdminIntegerFieldWidget())
    if tipo == 'decimal':
        return forms.DecimalField(**kwargs, max_digits=14, decimal_places=2, widget=UnfoldAdminDecimalFieldWidget())
    if tipo == 'data':
        return forms.DateField(**kwargs, widget=UnfoldAdminSingleDateWidget())
    if tipo == 'booleano':
        return forms.NullBooleanField(label=label, required=False, widget=UnfoldAdminNullBooleanSelectWidget())
    return forms.CharField(**kwargs, widget=UnfoldAdminTextInputWidget())


class DynamicSchemaFormMixin:
    """
    Mixin para ModelForm com um JSONField cujo conteúdo depende de um campo discriminador.

    Atributos de configuração (definir na subclasse):
        schema              dict: schema completo {chave: [descritores]}
        discriminator_field str:  nome do campo que seleciona o schema (default: 'tipo')
        metadados_field     str:  nome do JSONField na model (default: 'metadados')
        meta_prefix         str:  prefixo dos campos dinâmicos (default: 'meta_')

    A subclasse deve excluir o `metadados_field` via Meta.exclude para evitar conflito.
    """

    schema = {}
    discriminator_field = 'tipo'
    metadados_field = 'metadados'
    meta_prefix = 'meta_'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        prefix = self.meta_prefix
        schema = self.schema

        if self.discriminator_field in self.fields:
            # fill: Alpine lê o valor atual do elemento quando o dado reativo é null/vazio,
            # evitando que o x-data (inicializado com null pelo Unfold) sobrescreva o valor
            # renderizado pelo Django (necessário para mostrar campos ao editar registros).
            self.fields[self.discriminator_field].widget.attrs['x-model.fill'] = self.discriminator_field

        meta_info = build_meta_info(schema)
        for campo, info in meta_info.items():
            self.fields[f'{prefix}{campo}'] = make_schema_form_field(info)

        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            json_val = getattr(instance, self.metadados_field, None) or {}
            for campo in meta_info:
                val = json_val.get(campo)
                if val is None:
                    continue
                field = self.fields[f'{prefix}{campo}']
                self.initial[f'{prefix}{campo}'] = self._deserialize_meta_value(field, val)

    def _deserialize_meta_value(self, field, val):
        if isinstance(field, forms.DateField) and isinstance(val, str):
            try:
                return date.fromisoformat(val)
            except ValueError:
                return val
        if isinstance(field, forms.DecimalField) and isinstance(val, str):
            try:
                return Decimal(val)
            except InvalidOperation:
                return val
        return val

    def clean(self):
        cleaned = super().clean()
        prefix = self.meta_prefix
        tipo = cleaned.get(self.discriminator_field)
        schema = self.schema.get(tipo, [])
        errors = {}
        for campo_info in schema:
            if campo_info['obrigatorio']:
                val = cleaned.get(f'{prefix}{campo_info["campo"]}')
                if val is None or val == '':
                    errors[f'{prefix}{campo_info["campo"]}'] = (
                        f'{campo_info["label"]} é obrigatório para este tipo.'
                    )
        if errors:
            raise forms.ValidationError(errors)
        return cleaned

    def _collect_metadados(self):
        prefix = self.meta_prefix
        meta = {}
        for campo in build_meta_info(self.schema):
            val = self.cleaned_data.get(f'{prefix}{campo}')
            if val is None or val == '':
                continue
            if isinstance(val, date):
                meta[campo] = val.isoformat()
            elif isinstance(val, Decimal):
                meta[campo] = str(val)
            else:
                meta[campo] = val
        return meta

    def save(self, commit=True):
        instance = super().save(commit=False)
        setattr(instance, self.metadados_field, self._collect_metadados())
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class DynamicSchemaAdminMixin:
    """
    Mixin para ModelAdmin que usa DynamicSchemaFormMixin no formulário.

    O modelform_factory (chamado dentro de get_form) valida cada nome de campo dos
    fieldsets contra os campos reais da model. Os campos meta_* não existem na model —
    são adicionados dinamicamente pelo DynamicSchemaFormMixin.__init__ — então a validação
    levantaria FieldError. Este mixin intercepta a lista de campos (que o Django passa
    explicitamente como fields=flatten_fieldsets(...) no change_view) e remove os meta_* e
    readonly antes de repassar ao super(). O __init__ do form ainda adiciona os meta_* de
    volta, e os fieldsets os referenciam pelo nome, então continuam sendo renderizados.

    Requer que `meta_prefix` da subclasse do formulário esteja alinhado com `_meta_prefix`
    aqui (default: 'meta_').
    """

    _meta_prefix = 'meta_'
    _extra_form_fields: list = []  # campos não-model adicionados ao form (ex: campos de GenericFK interativa)

    def get_form(self, request, obj=None, change=False, **kwargs):
        all_fields = kwargs.pop('fields', None) or flatten_fieldsets(self.get_fieldsets(request, obj))
        readonly = set(self.get_readonly_fields(request, obj))
        extra = set(self._extra_form_fields)
        prefix = self._meta_prefix
        kwargs['fields'] = [
            f for f in all_fields
            if not f.startswith(prefix) and f not in readonly and f not in extra
        ]
        return super().get_form(request, obj, change, **kwargs)
