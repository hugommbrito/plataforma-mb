from unfold.widgets import UnfoldAdminTextInputWidget


class CpfCnpjWidget(UnfoldAdminTextInputWidget):
    class Media:
        js = ('pessoas/js/cpf_cnpj_mask.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs['data-cpf-cnpj-mask'] = '1'
        self.attrs['placeholder'] = '000.000.000-00'
        self.attrs['maxlength'] = '18'

    def format_value(self, value):
        if value:
            digits = ''.join(filter(str.isdigit, str(value)))
            if len(digits) == 11:
                return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}'
            if len(digits) == 14:
                return f'{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}'
        return super().format_value(value)
