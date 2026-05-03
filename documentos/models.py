import os
from datetime import date

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


def _nome_entidade(obj):
    """Retorna o nome legível da entidade vinculada ao documento."""
    model_label = obj.__class__.__name__.lower()

    nomes = {
        'imovel':             lambda o: o.nome,
        'contrato':           lambda o: o.imovel.nome,
        'pessoa':             lambda o: o.apelido or o.nome,
        'perfilproprietario': lambda o: o.pessoa.apelido or o.pessoa.nome,
        'perfilcliente':      lambda o: o.pessoa.apelido or o.pessoa.nome,
        'perfilimobiliaria':  lambda o: o.pessoa.nome,
        'perfilfíador':       lambda o: o.pessoa.apelido or o.pessoa.nome,
    }
    return nomes.get(model_label, lambda o: str(o))(obj)


def _documento_upload_path(instance, filename):
    """Monta caminho e nome do arquivo com base na entidade vinculada e no tipo do documento."""
    _, ext = os.path.splitext(filename)
    tipo_display = dict(Documento.Tipo.choices).get(instance.tipo, instance.tipo)
    tipo_pasta = slugify(tipo_display) if tipo_display else 'outro'

    obj = instance.content_object
    if obj is None:
        return f'documentos/sem-vinculo/{tipo_pasta}/{date.today().strftime("%Y.%m.%d")} - {tipo_display}{ext.lower()}'

    model_label = obj.__class__.__name__.lower()
    nome = _nome_entidade(obj)
    filename_final = f'{date.today().strftime("%Y.%m.%d")} - {tipo_display} - {nome}{ext.lower()}'

    def nome_slug(perfil):
        return slugify(perfil.pessoa.apelido or perfil.pessoa.nome)

    caminhos = {
        'imovel':             lambda o: f'imoveis/{slugify(o.nome)}',
        'contrato':           lambda o: f'imoveis/{slugify(o.imovel.nome)}/contratos/{slugify(o.cliente.pessoa.apelido or o.cliente.pessoa.nome)}',
        'pessoa':             lambda o: f'pessoas/{slugify(o.apelido or o.nome)}',
        'perfilproprietario': lambda o: f'pessoas/{nome_slug(o)}/perfil-proprietario',
        'perfilcliente':      lambda o: f'pessoas/{nome_slug(o)}/perfil-cliente',
        'perfilimobiliaria':  lambda o: f'pessoas/{nome_slug(o)}/perfil-imobiliaria',
        'perfilfíador':       lambda o: f'pessoas/{nome_slug(o)}/perfil-fiador',
    }

    base = caminhos.get(model_label, lambda _: f'documentos/{model_label}')(obj)
    return f'{base}/{tipo_pasta}/{filename_final}'


class Documento(models.Model):
    class Tipo(models.TextChoices):
        MATRICULA         = 'MA', 'Matrícula'
        ESCRITURA         = 'ES', 'Escritura'
        CONTRATO          = 'CO', 'Contrato'
        ADITIVO           = 'AD', 'Aditivo Contratual'
        COMPROVANTE       = 'CP', 'Comprovante de Pagamento'
        SEGURO            = 'SE', 'Seguro'
        PROCURACAO        = 'PR', 'Procuração'
        IPTU              = 'IP', 'IPTU'
        LICENCA           = 'LI', 'Licença / Alvará'
        IDENTIDADE        = 'ID', 'Documento de Identidade'
        COMPROVANTE_RENDA = 'CR', 'Comprovante de Renda'
        CONSULTA_CREDITO  = 'CC', 'Consulta de Score de Crédito'
        CND_MUNICIPAL     = 'CM', 'Município - CND'
        FICHA_CADASTRAL   = 'FC', 'Município - Ficha Cadastral'
        ESCRITURA_PUBLICA = 'EP', 'Cartório - Escritura Pública'
        CERTIDAO_REGISTRO = 'CE', 'Cartório - Certidão de Registro'
        CERTIDAO_INT_TEOR = 'CI', 'Cartório - Certidão de Inteiro Teor'
        OUTRO             = 'OU', 'Outro'

    # Schemas de metadados por tipo.
    # Cada campo: {'campo': str, 'label': str, 'tipo': texto|numero|decimal|data|booleano, 'obrigatorio': bool}
    # Usado em clean() para validar campos obrigatórios e como referência para renderização futura no admin.
    METADADOS_SCHEMA = {
        Tipo.MATRICULA: [
            {'campo': 'numero_matricula', 'label': 'Número da Matrícula', 'tipo': 'texto',   'obrigatorio': True},
            {'campo': 'cartorio',         'label': 'Cartório',            'tipo': 'texto',   'obrigatorio': True},
            {'campo': 'data_registro',    'label': 'Data de Registro',    'tipo': 'data',    'obrigatorio': False},
        ],
        Tipo.ESCRITURA: [
            {'campo': 'numero_escritura', 'label': 'Número da Escritura', 'tipo': 'texto',   'obrigatorio': True},
            {'campo': 'cartorio',         'label': 'Cartório',            'tipo': 'texto',   'obrigatorio': True},
            {'campo': 'data_registro',    'label': 'Data de Registro',    'tipo': 'data',    'obrigatorio': False},
            {'campo': 'valor_transacao',  'label': 'Valor da Transação',  'tipo': 'decimal', 'obrigatorio': False},
        ],
        Tipo.ADITIVO: [
            {'campo': 'numero_aditivo', 'label': 'Número do Aditivo', 'tipo': 'texto', 'obrigatorio': False},
            {'campo': 'motivo',         'label': 'Motivo do Aditivo', 'tipo': 'texto', 'obrigatorio': False},
        ],
        Tipo.COMPROVANTE: [
            {'campo': 'valor',            'label': 'Valor (R$)',          'tipo': 'decimal', 'obrigatorio': True},
            {'campo': 'data_pagamento',   'label': 'Data do Pagamento',   'tipo': 'data',    'obrigatorio': True},
            {'campo': 'banco',            'label': 'Banco / Instituição', 'tipo': 'texto',   'obrigatorio': False},
            {'campo': 'numero_transacao', 'label': 'Nº da Transação',     'tipo': 'texto',   'obrigatorio': False},
        ],
        Tipo.SEGURO: [
            {'campo': 'numero_apolice', 'label': 'Número da Apólice', 'tipo': 'texto',   'obrigatorio': True},
            {'campo': 'seguradora',     'label': 'Seguradora',         'tipo': 'texto',   'obrigatorio': True},
            {'campo': 'cobertura',      'label': 'Cobertura (R$)',     'tipo': 'decimal', 'obrigatorio': False},
        ],
        Tipo.PROCURACAO: [
            {'campo': 'numero_registro', 'label': 'Número de Registro', 'tipo': 'texto', 'obrigatorio': False},
            {'campo': 'cartorio',        'label': 'Cartório',            'tipo': 'texto', 'obrigatorio': False},
            {'campo': 'outorgante',      'label': 'Outorgante',          'tipo': 'texto', 'obrigatorio': True},
            {'campo': 'outorgado',       'label': 'Outorgado',           'tipo': 'texto', 'obrigatorio': True},
        ],
        Tipo.IPTU: [
            {'campo': 'numero_contribuinte', 'label': 'Nº do Contribuinte', 'tipo': 'texto',   'obrigatorio': True},
            {'campo': 'ano',                 'label': 'Ano de Referência',  'tipo': 'numero',  'obrigatorio': True},
            {'campo': 'parcela',             'label': 'Parcela',             'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'valor',               'label': 'Valor (R$)',          'tipo': 'decimal', 'obrigatorio': False},
        ],
        Tipo.LICENCA: [
            {'campo': 'numero_licenca', 'label': 'Número da Licença', 'tipo': 'texto', 'obrigatorio': True},
            {'campo': 'orgao_emissor',  'label': 'Órgão Emissor',      'tipo': 'texto', 'obrigatorio': True},
        ],
        Tipo.IDENTIDADE: [
            {'campo': 'numero_documento', 'label': 'Número do Documento', 'tipo': 'texto', 'obrigatorio': True},
            {'campo': 'orgao_emissor',    'label': 'Órgão Emissor',        'tipo': 'texto', 'obrigatorio': False},
            {'campo': 'data_expedicao',   'label': 'Data de Expedição',    'tipo': 'data',  'obrigatorio': False},
        ],
        Tipo.COMPROVANTE_RENDA: [
            {'campo': 'tipo_renda',   'label': 'Tipo de Renda',     'tipo': 'texto',   'obrigatorio': True},
            {'campo': 'valor_mensal', 'label': 'Valor Mensal (R$)', 'tipo': 'decimal', 'obrigatorio': True},
            {'campo': 'empregador',   'label': 'Empregador',         'tipo': 'texto',   'obrigatorio': False},
        ],
        Tipo.CONSULTA_CREDITO: [
            {'campo': 'bureau',        'label': 'Bureau (Serasa, SPC...)', 'tipo': 'texto',  'obrigatorio': True},
            {'campo': 'score',         'label': 'Score',                    'tipo': 'numero', 'obrigatorio': False},
            {'campo': 'data_consulta', 'label': 'Data da Consulta',         'tipo': 'data',   'obrigatorio': True},
        ],
    }

    arquivo = models.FileField(upload_to=_documento_upload_path)
    tipo = models.CharField(max_length=2, choices=Tipo.choices)
    descricao = models.CharField('descrição', max_length=200, blank=True)
    vencimento = models.DateField(
        null=True, blank=True,
        help_text='Preencher para documentos com prazo (seguro, procuração, licença).'
    )
    metadados = models.JSONField(
        default=dict, blank=True,
        help_text='Campos extras específicos do tipo. Ex: {"numero_apolice": "...", "seguradora": "..."}'
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'documento'
        verbose_name_plural = 'documentos'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.descricao or self.arquivo.name}'

    def clean(self):
        tipos_com_vencimento = {self.Tipo.SEGURO, self.Tipo.PROCURACAO, self.Tipo.LICENCA}
        if self.tipo in tipos_com_vencimento and not self.vencimento:
            raise ValidationError({
                'vencimento': f'Vencimento obrigatório para documentos do tipo "{self.get_tipo_display()}".'
            })
