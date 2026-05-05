from decimal import Decimal

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from pessoas.models import PerfilProprietario, Pessoa


class Imovel(models.Model):
    class Tipo(models.TextChoices):
        APARTAMENTO = 'AP', 'Apartamento'
        CASA = 'CA', 'Casa'
        SALA_COMERCIAL = 'SC', 'Sala Comercial'
        IMOVEL_COMERCIAL = 'IC', 'Imóvel Comercial'
        GALPAO = 'GA', 'Galpão'
        TERRENO = 'TE', 'Terreno'
        OUTRO = 'OU', 'Outro'

    CARACTERISTICAS_SCHEMA = {
        Tipo.APARTAMENTO: [
            {'campo': 'andar',             'label': 'Andar',                  'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'numero_unidade',    'label': 'Número da Unidade',      'tipo': 'texto',   'obrigatorio': False},
            {'campo': 'quartos',           'label': 'Quartos',                'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'banheiros',         'label': 'Banheiros',              'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'vagas',             'label': 'Vagas de Garagem',       'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'condominio_mensal', 'label': 'Condomínio Mensal (R$)', 'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'tem_varanda',        'label': 'Possui Varanda',          'tipo': 'booleano','obrigatorio': False},
        ],
        Tipo.CASA: [
            {'campo': 'quartos',           'label': 'Quartos',                'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'banheiros',         'label': 'Banheiros',              'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'area_construida',   'label': 'Área Construída (m²)',   'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'area_terreno',      'label': 'Área do Terreno (m²)',   'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'pavimentos',        'label': 'Pavimentos',             'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'vagas',             'label': 'Vagas de Garagem',       'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'tem_piscina',       'label': 'Possui Piscina',         'tipo': 'booleano','obrigatorio': False},
            {'campo': 'tem_edicula',       'label': 'Possui Edícula',         'tipo': 'booleano','obrigatorio': False},
        ],
        Tipo.SALA_COMERCIAL: [
            {'campo': 'andar',             'label': 'Andar',                  'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'numero_unidade',    'label': 'Número da Unidade',      'tipo': 'texto',   'obrigatorio': False},
            {'campo': 'condominio_mensal', 'label': 'Condomínio Mensal (R$)', 'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'vagas_cobertas',    'label': 'Vagas Cobertas',         'tipo': 'numero',  'obrigatorio': False},
        ],
        Tipo.IMOVEL_COMERCIAL: [
            {'campo': 'area_construida',   'label': 'Área Construída (m²)',   'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'area_terreno',      'label': 'Área do Terreno (m²)',   'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'pe_direito',        'label': 'Pé Direito (m)',         'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'banheiros',         'label': 'Banheiros',              'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'vagas_proprias',    'label': 'Vagas Próprias',         'tipo': 'numero',  'obrigatorio': False},
        ],
        Tipo.GALPAO: [
            {'campo': 'area_construida',   'label': 'Área Construída (m²)',   'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'area_terreno',      'label': 'Área do Terreno (m²)',   'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'area_escritorio',   'label': 'Área de Escritório (m²)','tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'docas',             'label': 'Docas',                  'tipo': 'numero',  'obrigatorio': False},
            {'campo': 'pe_direito',        'label': 'Pé Direito (m)',         'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'piso_tipo',         'label': 'Tipo de Piso',           'tipo': 'texto',   'obrigatorio': False},
        ],
        Tipo.TERRENO: [
            {'campo': 'frente',           'label': 'Frente (m)',            'tipo': 'decimal', 'obrigatorio': False},
            {'campo': 'zoneamento',        'label': 'Zoneamento',             'tipo': 'texto',   'obrigatorio': False},
            {'campo': 'topografia',        'label': 'Topografia',             'tipo': 'texto',   'obrigatorio': False},
        ],
    }

    class Status(models.TextChoices):
        DISPONIVEL = 'DI', 'Disponível'
        ALUGADO = 'AL', 'Alugado'
        VENDA = 'VE', 'À Venda'
        REFORMA = 'RE', 'Em Reforma'
        INATIVO = 'IN', 'Inativo'
        GESTAO_TERCEIRO = 'GT', 'Gerido por terceiros'

    # Identificação
    nome = models.CharField(max_length=200, help_text='Nome de referência interno (ex: "Apto Centro")')
    tipo = models.CharField(max_length=2, choices=Tipo.choices)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.DISPONIVEL)
    area = models.DecimalField(
        'área (m²)', max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Localização
    endereco = models.CharField('endereço', max_length=300, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2)
    cidade = models.CharField(max_length=100, verbose_name="Município")
    cep = models.CharField('CEP', max_length=9, blank=True)

    # Características
    caracteristicas = models.JSONField(
        default=dict, blank=True,
        help_text='Campos específicos do tipo de imóvel.'
    )

    # Financeiro
    valor_mercado = models.DecimalField(
        'valor de mercado (R$)', max_digits=14, decimal_places=2, null=True, blank=True
    )

    # Dados do Município
    matricula_municipio = models.CharField('Matrícula do imóvel na prefeitura', max_length=50, blank=True)
    inscricao_municipal = models.CharField('Inscrição Municipal', max_length=50, blank=True)

    # Dados do Cartório
    matricula_cartorio = models.CharField('Matrícula do imóvel no cartorio', max_length=50, blank=True)
    titular_registro = models.ForeignKey(
        Pessoa,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='imoveis_como_titular',
        verbose_name='titular do registro',
        help_text='Pessoa em cujo nome a matrícula está lavrada no cartório.',
    )


    observacoes = models.TextField('observações', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    documentos = GenericRelation('documentos.Documento')
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'imóvel'
        verbose_name_plural = 'Imóveis'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} — {self.cidade}/{self.estado}'

    @property
    def valor_por_m2(self):
        if self.valor_mercado and self.area:
            return round(self.valor_mercado / self.area, 2)
        return None

    @property
    def participacao_interna_pct(self):
        """Soma das participações (0–1) dos proprietários com interno=True."""
        return sum(
            ip.participacao
            for ip in self.imovelproprietario_set.select_related('proprietario')
            if ip.proprietario.interno
        )

    @property
    def valor_interno(self):
        """Valor de mercado correspondente à participação interna (R$)."""
        if self.valor_mercado:
            return round(self.valor_mercado * self.participacao_interna_pct, 2)
        return None

    @property
    def registro_regularizado(self):
        """
        None  → titular não informado.
        True  → titular consta como um dos proprietários do imóvel.
        False → titular não está entre os proprietários (registro pendente de regularização).
        """
        if not self.titular_registro_id:
            return None
        ids_proprietarios = {
            ip.proprietario.pessoa_id
            for ip in self.imovelproprietario_set.select_related('proprietario')
        }
        return self.titular_registro_id in ids_proprietarios

    @property
    def proprietarios_lista(self):
        return self.imovelproprietario_set.select_related('proprietario__pessoa').all()


class ImovelProprietario(models.Model):
    imovel = models.ForeignKey(Imovel, on_delete=models.PROTECT)
    proprietario = models.ForeignKey(PerfilProprietario, on_delete=models.PROTECT)
    participacao = models.DecimalField(
        'participação (%)', max_digits=5, decimal_places=4,
        help_text='Ex: 0.5000 = 50%. A soma de todos os proprietários deve ser 1.'
    )

    class Meta:
        verbose_name = 'proprietário do imóvel'
        verbose_name_plural = 'proprietários do imóvel'
        unique_together = [('imovel', 'proprietario')]

    def __str__(self):
        pct = f'{self.participacao * 100:.2f}%'
        return f'{self.proprietario.pessoa.nome} — {pct}'

    def clean(self):
        if self.participacao is not None and (
            self.participacao <= Decimal('0') or self.participacao > Decimal('1')
        ):
            raise ValidationError({'participacao': 'Participação deve ser entre 0 e 100%.'})

        # valida soma total das participações do imóvel
        if self.imovel_id:
            outras = ImovelProprietario.objects.filter(imovel=self.imovel_id)
            if self.pk:
                outras = outras.exclude(pk=self.pk)
            soma = sum(o.participacao for o in outras) + (self.participacao or Decimal('0'))
            if soma > Decimal('1'):
                raise ValidationError(
                    {'participacao': f'A soma das participações seria {soma * 100:.2f}%, ultrapassando 100%.'}
                )
