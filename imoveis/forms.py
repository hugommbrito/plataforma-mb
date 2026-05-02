from django import forms

from .models import Imovel
from .widgets import CidadeWidget, EstadoWidget


class ImovelForm(forms.ModelForm):
    estado = forms.CharField(widget=EstadoWidget, max_length=2)
    cidade = forms.CharField(widget=CidadeWidget, max_length=100)

    class Meta:
        model = Imovel
        fields = '__all__'
