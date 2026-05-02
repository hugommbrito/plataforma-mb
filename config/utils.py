from calendar import monthrange
from datetime import date


def add_months(d: date, months: int) -> date:
    """Soma `months` meses a uma data, ajustando o dia ao último do mês se necessário."""
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def formatar_moeda(valor):
    """Formata um valor Decimal/float como moeda brasileira. Ex: 1234.5 → 'R$ 1.234,50'"""
    if valor is None:
        return '—'
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

def formatar_percentual(valor, casas_decimais=2):
    """Formata um valor decimal (0–1) como percentual. Ex: 0.75 → '75,00%'"""
    if valor is None:
        return '—'
    return f'{valor * 100:.{casas_decimais}f}%'.replace('.', ',')