from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from documentos.admin import (
    PessoaDocumentoInline,
    PerfilProprietarioDocumentoInline,
    PerfilClienteDocumentoInline,
    PerfilImobiliariaDocumentoInline,
    PerfilFiadorDocumentoInline,
)
from .forms import PessoaForm
from .models import (
    Pessoa,
    PerfilProprietario,
    PerfilCliente,
    PerfilImobiliaria,
    PerfilFiador,
)


class PerfilProprietarioInline(StackedInline):
    model = PerfilProprietario
    extra = 0
    can_delete = False
    fields = ['interno']


class PerfilClienteInline(StackedInline):
    model = PerfilCliente
    extra = 0
    can_delete = False
    fields = ['profissao', 'renda_mensal', 'observacoes']


class PerfilImobiliariaInline(StackedInline):
    model = PerfilImobiliaria
    extra = 0
    can_delete = False
    fields = ['creci', 'contato_responsavel', 'observacoes']


class PerfilFiadorInline(StackedInline):
    model = PerfilFiador
    extra = 0
    can_delete = False
    fields = ['profissao', 'renda_mensal', 'observacoes']


@admin.register(Pessoa)
class PessoaAdmin(ModelAdmin):
    form = PessoaForm
    list_display = ['nome', 'apelido', 'cpf_cnpj_formatado', 'tipo', 'telefone', 'email', 'papeis', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'apelido', 'cpf_cnpj', 'email']
    list_display_links = ['nome']
    inlines = [
        PerfilProprietarioInline,
        PerfilClienteInline,
        PerfilImobiliariaInline,
        PerfilFiadorInline,
        PessoaDocumentoInline,
    ]
    fieldsets = [
        ('Identificação', {'fields': ['tipo', 'nome', 'apelido', 'cpf_cnpj', 'ativo']}),
        ('Contato', {'fields': ['email', 'telefone', 'endereco']}),
        ('Observações', {'fields': ['observacoes'], 'classes': ['collapse']}),
    ]

    @admin.display(description='CPF / CNPJ')
    def cpf_cnpj_formatado(self, obj):
        d = obj.cpf_cnpj
        if len(d) == 11:
            return f'{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}'
        if len(d) == 14:
            return f'{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}'
        return d

    @admin.display(description='Papéis')
    def papeis(self, obj):
        roles = []
        if hasattr(obj, 'perfil_proprietario'):
            roles.append('Proprietário')
        if hasattr(obj, 'perfil_cliente'):
            roles.append('Cliente')
        if hasattr(obj, 'perfil_imobiliaria'):
            roles.append('Imobiliária')
        if hasattr(obj, 'perfil_fiador'):
            roles.append('Fiador')
        return ', '.join(roles) if roles else '—'


@admin.register(PerfilProprietario)
class PerfilProprietarioAdmin(ModelAdmin):
    list_display = ['pessoa', 'interno']
    list_filter = ['interno']
    search_fields = ['pessoa__nome', 'pessoa__cpf_cnpj']
    autocomplete_fields = ['pessoa']
    inlines = [PerfilProprietarioDocumentoInline]


@admin.register(PerfilCliente)
class PerfilClienteAdmin(ModelAdmin):
    list_display = ['pessoa', 'profissao', 'renda_mensal']
    search_fields = ['pessoa__nome', 'pessoa__cpf_cnpj']
    autocomplete_fields = ['pessoa']
    inlines = [PerfilClienteDocumentoInline]


@admin.register(PerfilImobiliaria)
class PerfilImobiliariaAdmin(ModelAdmin):
    list_display = ['pessoa', 'creci', 'contato_responsavel']
    search_fields = ['pessoa__nome', 'pessoa__cpf_cnpj']
    autocomplete_fields = ['pessoa']
    inlines = [PerfilImobiliariaDocumentoInline]


@admin.register(PerfilFiador)
class PerfilFiadorAdmin(ModelAdmin):
    list_display = ['pessoa', 'profissao', 'renda_mensal']
    search_fields = ['pessoa__nome', 'pessoa__cpf_cnpj']
    autocomplete_fields = ['pessoa']
    inlines = [PerfilFiadorDocumentoInline]
