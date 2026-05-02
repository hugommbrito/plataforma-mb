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