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


class _PerfilReadonlyInline(StackedInline):
    extra = 0
    # can_delete = False
    tab = True

    # def has_add_permission(self, _request, _obj=None):
    #     return False


class PerfilProprietarioInline(_PerfilReadonlyInline):
    model = PerfilProprietario
    # readonly_fields = ['interno']
    fields = ['interno']


class PerfilClienteInline(_PerfilReadonlyInline):
    model = PerfilCliente
    fields = ['profissao', 'renda_mensal', 'observacoes']


class PerfilImobiliariaInline(_PerfilReadonlyInline):
    model = PerfilImobiliaria
    fields = ['creci', 'contato_responsavel', 'observacoes']


class PerfilFiadorInline(_PerfilReadonlyInline):
    model = PerfilFiador
    fields = ['profissao', 'renda_mensal', 'observacoes']


class _PessoaDocumentoTabInline(PessoaDocumentoInline):
    tab = True


@admin.register(Pessoa)
class PessoaAdmin(ModelAdmin):
    form = PessoaForm
    list_display = ['nome', 'apelido', 'cpf_cnpj_formatado', 'tipo', 'telefone', 'email', 'papeis', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'apelido', 'cpf_cnpj', 'email']
    list_display_links = ['nome']
    fieldsets = [
        ('Identificação', {'fields': ['tipo', 'nome', 'apelido', 'cpf_cnpj', 'ativo']}),
        ('Contato', {'fields': ['email', 'telefone', 'endereco']}),
        ('Observações', {'fields': ['observacoes']}),
    ]

    def get_inlines(self, _request, obj=None):
        if obj is None:
            return [_PessoaDocumentoTabInline]
        inlines = []
        if hasattr(obj, 'perfil_proprietario'):
            inlines.append(PerfilProprietarioInline)
        if hasattr(obj, 'perfil_cliente'):
            inlines.append(PerfilClienteInline)
        if hasattr(obj, 'perfil_imobiliaria'):
            inlines.append(PerfilImobiliariaInline)
        if hasattr(obj, 'perfil_fiador'):
            inlines.append(PerfilFiadorInline)
        inlines.append(_PessoaDocumentoTabInline)
        return inlines

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
