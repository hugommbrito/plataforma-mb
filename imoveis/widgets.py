import json

from django.utils.safestring import mark_safe
from unfold.widgets import UnfoldAdminTextInputWidget

ESTADOS_BR = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
]


class EstadoWidget(UnfoldAdminTextInputWidget):
    def __init__(self, attrs=None):
        super().__init__(attrs={'maxlength': '2', 'style': 'text-transform: uppercase;', **(attrs or {})})

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        list_id = f'datalist_{name}'
        attrs['list'] = list_id
        input_html = super().render(name, value, attrs, renderer)
        options = ''.join(f'<option value="{uf}">' for uf in ESTADOS_BR)
        datalist = f'<datalist id="{list_id}">{options}</datalist>'
        return mark_safe(input_html + datalist)


class CidadeWidget(UnfoldAdminTextInputWidget):
    class Media:
        js = ('imoveis/js/cidade_estado_filter.js',)

    def render(self, name, value, attrs=None, renderer=None):
        from .models import Imovel
        attrs = attrs or {}
        list_id = f'datalist_{name}'
        attrs['list'] = list_id
        attrs['data-cidade-field'] = '1'
        input_html = super().render(name, value, attrs, renderer)

        pares = (
            Imovel.objects
            .exclude(cidade='')
            .exclude(estado='')
            .values_list('estado', 'cidade')
            .distinct()
            .order_by('estado', 'cidade')
        )
        cidades_por_estado = {}
        for estado, cidade in pares:
            cidades_por_estado.setdefault(estado, []).append(cidade)

        data_json = json.dumps(cidades_por_estado, ensure_ascii=False)
        datalist = f'<datalist id="{list_id}"></datalist>'
        data_script = f'<script>window.__cidadesPorEstado = {data_json};</script>'

        return mark_safe(input_html + datalist + data_script)
