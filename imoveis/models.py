from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from pessoas.models import PerfilProprietario


class Imovel(models.Model):
    class Tipo(models.TextChoices):
        APARTAMENTO = 'AP', 'Apartamento'
        CASA = 'CA', 'Casa'
        SALA_COMERCIAL = 'SC', 'Sala Comercial'
        IMOVEL_COMERCIAL = 'IC', 'Imóvel Comercial'
        GALPAO = 'GA', 'Galpão'
        TERRENO = 'TE', 'Terreno'
        OUTRO = 'OU', 'Outro'

    class Status(models.TextChoices):
        DISPONIVEL = 'DI', 'Disponível'
        ALUGADO = 'AL', 'Alugado'
        VENDA = 'VE', 'À Venda'
        REFORMA = 'RE', 'Em Reforma'
        INATIVO = 'IN', 'Inativo'

    # Identificação
    nome = models.CharField(max_length=200, help_text='Nome de referência interno (ex: "Apto Centro")')
    tipo = models.CharField(max_length=2, choices=Tipo.choices)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.DISPONIVEL)

    # Localização
    endereco = models.CharField('endereço', max_length=300, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2)
    cidade = models.CharField(max_length=100)
    cep = models.CharField('CEP', max_length=9, blank=True)

    # Características
    area_total = models.DecimalField(
        'área total (m²)', max_digits=10, decimal_places=2, null=True, blank=True
    )
    quartos = models.PositiveSmallIntegerField(null=True, blank=True)
    vagas = models.PositiveSmallIntegerField('vagas de garagem', null=True, blank=True)

    # Financeiro
    valor_mercado = models.DecimalField(
        'valor de mercado (R$)', max_digits=14, decimal_places=2, null=True, blank=True
    )
    matricula = models.CharField('matrícula do imóvel', max_length=50, blank=True)

    observacoes = models.TextField('observações', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'imóvel'
        verbose_name_plural = '.imóveis'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} — {self.cidade}/{self.estado}'

    @property
    def valor_por_m2(self):
        if self.valor_mercado and self.area_total:
            return round(self.valor_mercado / self.area_total, 2)
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
