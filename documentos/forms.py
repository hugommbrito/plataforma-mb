from django import forms

from config.dynamic_form import DynamicSchemaFormMixin
from .models import Documento


class DocumentoForm(DynamicSchemaFormMixin, forms.ModelForm):
    schema = Documento.METADADOS_SCHEMA

    class Meta:
        model = Documento
        exclude = ['metadados']
