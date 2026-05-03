from datetime import date

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from config.utils import add_months
from imoveis.models import Imovel
from pessoas.models import PerfilCliente, PerfilFiador, PerfilImobiliaria


class Contrato(models.Model):
    class Indice(models.TextChoices):
        IGPM = 'IGPM', 'IGP-M'
        IPCA = 'IPCA', 'IPCA'
        INCC = 'INCC', 'INCC'
        FIXO = 'FIXO', 'Fixo (sem reajuste)'
        OUTRO = 'OUTRO', 'Outro índice'

    imovel = models.ForeignKey(Imovel, on_delete=models.PROTECT, related_name='contratos')
    cliente = models.ForeignKey(PerfilCliente, on_delete=models.PROTECT, related_name='contratos')
    imobiliaria = models.ForeignKey(
        PerfilImobiliaria, on_delete=models.PROTECT,
        related_name='contratos', null=True, blank=True
    )

    data_inicio = models.DateField('data de início')
    vigencia = models.IntegerField('Vigência em meses')
    renovacao_automatica = models.BooleanField('Renovação automatica?', default=False)
    quant_renov_automaticas = models.PositiveSmallIntegerField('Quantidade de renovações automáticas permitidas', default=0)

    valor_aluguel = models.DecimalField('valor do aluguel (R$)', max_digits=12, decimal_places=2)
    indice_reajuste = models.CharField(
        'índice de reajuste', max_length=5, choices=Indice.choices, default=Indice.IGPM
    )
    dia_vencimento = models.PositiveSmallIntegerField(
        'dia de vencimento', help_text='Dia do mês em que o aluguel vence (1–28).'
    )
    rescindido_em = models.DateField('rescindido em', null=True, blank=True)
    observacoes = models.TextField('observações', blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    documentos = GenericRelation('documentos.Documento')
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'contrato'
        verbose_name_plural = '.contratos'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'{self.imovel.nome} — {self.cliente.pessoa.apelido} ({self.data_inicio:%m/%Y})'

    @property
    def data_fim(self):
        """Término do contrato considerando vigência e todas as renovações automáticas."""
        if not self.data_inicio or not self.vigencia:
            return None
        meses_totais = self.vigencia
        if self.renovacao_automatica and self.quant_renov_automaticas:
            meses_totais += self.vigencia * self.quant_renov_automaticas
        return add_months(self.data_inicio, meses_totais)

    @property
    def status(self):
        if self.rescindido_em:
            return 'Rescindido'
        if not self.data_inicio or not self.vigencia:
            return '—'
        hoje = date.today()
        if hoje < self.data_inicio:
            return 'Futuro'
        if hoje <= add_months(self.data_inicio, self.vigencia):
            return 'Ativo'
        if hoje <= self.data_fim:
            return 'Renovado'
        return 'Vencido'

    @property
    def historico_precos(self):
        """Períodos de vigência de cada valor de aluguel, detectados via histórico de alterações."""
        registros = list(self.history.order_by('history_date'))
        if not registros:
            return []

        periodos = []
        valor_atual = registros[0].valor_aluguel
        inicio_atual = self.data_inicio  # primeiro período começa na data contratual, não no timestamp

        for registro in registros[1:]:
            if registro.valor_aluguel != valor_atual:
                periodos.append({
                    'valor': valor_atual,
                    'inicio': inicio_atual,
                    'fim': registro.history_date.date(),
                })
                valor_atual = registro.valor_aluguel
                inicio_atual = registro.history_date.date()

        periodos.append({'valor': valor_atual, 'inicio': inicio_atual, 'fim': None})
        return periodos

    def clean(self):
        if self.vigencia is not None and self.vigencia <= 0:
            raise ValidationError({'vigencia': 'A vigência deve ser de pelo menos 1 mês.'})
        if self.dia_vencimento and not (1 <= self.dia_vencimento <= 28):
            raise ValidationError({'dia_vencimento': 'O dia de vencimento deve ser entre 1 e 28.'})
        if self.rescindido_em and self.data_inicio and self.rescindido_em < self.data_inicio:
            raise ValidationError({'rescindido_em': 'A data de rescisão não pode ser anterior ao início do contrato.'})


class Garantia(models.Model):
    class Tipo(models.TextChoices):
        FIADOR = 'FI', 'Fiador'
        DEPOSITO = 'DE', 'Depósito Caução'
        SEGURO = 'SE', 'Seguro'
        SEM_GARANTIA = 'SG', 'Contrato sem Garantias'

    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='garantias')
    tipo = models.CharField(max_length=2, choices=Tipo.choices)
    fiador = models.ForeignKey(
        PerfilFiador, on_delete=models.PROTECT,
        related_name='garantias', null=True, blank=True
    )
    valor = models.DecimalField(
        'valor (R$)', max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Valor do depósito, prêmio do seguro ou título de capitalização.'
    )
    observacoes = models.TextField('observações', blank=True)

    class Meta:
        verbose_name = 'garantia'
        verbose_name_plural = 'garantias'

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.contrato}'

    def clean(self):
        if self.tipo == self.Tipo.FIADOR and not self.fiador_id:
            raise ValidationError({'fiador': 'Informe o fiador para garantia do tipo Fiador.'})
        if self.tipo != self.Tipo.FIADOR and self.fiador_id:
            raise ValidationError({'fiador': 'Fiador só é aplicável quando o tipo for "Fiador".'})
