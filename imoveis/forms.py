from django import forms

from config.dynamic_form import DynamicSchemaFormMixin
from .models import Imovel
from .widgets import EstadoWidget, MunicipioWidget


class ImovelForm(DynamicSchemaFormMixin, forms.ModelForm):
    schema = Imovel.CARACTERISTICAS_SCHEMA
    metadados_field = 'caracteristicas'

    estado = forms.CharField(widget=EstadoWidget, max_length=2)
    municipio = forms.CharField(widget=MunicipioWidget, max_length=100)

    class Meta:
        model = Imovel
        exclude = ['caracteristicas']
