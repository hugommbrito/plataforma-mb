from django.db import models
from django.core.validators import RegexValidator


class Pessoa(models.Model):
    class Tipo(models.TextChoices):
        PF = 'PF', 'Pessoa Física'
        PJ = 'PJ', 'Pessoa Jurídica'

    tipo = models.CharField(max_length=2, choices=Tipo.choices, default=Tipo.PF)
    nome = models.CharField(max_length=200)
    apelido = models.CharField(max_length=200, blank=True)
    # Armazena apenas dígitos (11 = CPF, 14 = CNPJ). Formatação feita no widget.
    cpf_cnpj = models.CharField(
        max_length=14,
        unique=True,
        blank=True,
        validators=[RegexValidator(r'^\d{11}$|^\d{14}$', 'Informe 11 dígitos (CPF) ou 14 dígitos (CNPJ).')],
    )
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.CharField('endereço', max_length=300, blank=True)
    observacoes = models.TextField('observações', blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'pessoa'
        verbose_name_plural = '.pessoas (PFs e PJs)'
        ordering = ['nome']

    def __str__(self):
        return f'{self.apelido} ({self.cpf_cnpj})' if self.cpf_cnpj else self.apelido


# Usado em: ImovelProprietario (participação no imóvel), recibo de aluguel, relatório de IR, DRE por imóvel.
class PerfilProprietario(models.Model):
    pessoa = models.OneToOneField(
        Pessoa, on_delete=models.PROTECT, related_name='perfil_proprietario'
    )
    # Indica se é proprietário da família (holding). Usado para calcular participação interna por imóvel.
    interno = models.BooleanField(
        default=False,
        help_text='Marque se este proprietário faz parte da família/holding.'
    )

    class Meta:
        verbose_name = 'perfil proprietário'
        verbose_name_plural = 'perfis proprietários'

    def __str__(self):
        return f'Proprietário: {self.pessoa.nome}'


# Usado em: Contrato.cliente (inquilino do imóvel), histórico de contratos, carnê-leão.
class PerfilCliente(models.Model):
    pessoa = models.OneToOneField(
        Pessoa, on_delete=models.PROTECT, related_name='perfil_cliente'
    )
    profissao = models.CharField('profissão', max_length=100, blank=True)
    renda_mensal = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    observacoes = models.TextField('observações', blank=True)

    class Meta:
        verbose_name = 'perfil cliente (inquilino)'
        verbose_name_plural = 'perfis clientes (inquilinos)'

    def __str__(self):
        return f'Cliente: {self.pessoa.nome}'


# Usado em: Contrato.imobiliaria (intermediadora), cálculo de taxa de administração sobre o aluguel.
class PerfilImobiliaria(models.Model):
    pessoa = models.OneToOneField(
        Pessoa, on_delete=models.PROTECT, related_name='perfil_imobiliaria'
    )
    creci = models.CharField('CRECI', max_length=30, blank=True)
    contato_responsavel = models.CharField('contato responsável', max_length=200, blank=True)
    observacoes = models.TextField('observações', blank=True)

    class Meta:
        verbose_name = 'perfil imobiliária'
        verbose_name_plural = 'perfis imobiliárias'

    def __str__(self):
        return f'Imobiliária: {self.pessoa.nome}'


# Usado em: Garantia.fiador (garantia do contrato), checklist de documentação pré-contrato.
class PerfilFiador(models.Model):
    pessoa = models.OneToOneField(
        Pessoa, on_delete=models.PROTECT, related_name='perfil_fiador'
    )
    profissao = models.CharField('profissão', max_length=100, blank=True)
    renda_mensal = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    observacoes = models.TextField('observações', blank=True)

    class Meta:
        verbose_name = 'perfil fiador'
        verbose_name_plural = 'perfis fiadores'

    def __str__(self):
        return f'Fiador: {self.pessoa.nome}'
