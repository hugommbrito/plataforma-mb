from django import forms

from .widgets import CpfCnpjWidget


class CpfCnpjField(forms.CharField):
    widget = CpfCnpjWidget

    def to_python(self, value):
        value = super().to_python(value)
        return ''.join(filter(str.isdigit, value)) if value else value

    def validate(self, value):
        super().validate(value)
        if value and len(value) not in (11, 14):
            raise forms.ValidationError(
                'CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos.'
            )


class PessoaForm(forms.ModelForm):
    cpf_cnpj = CpfCnpjField(label='CPF / CNPJ', required=False)

    class Meta:
        from .models import Pessoa
        model = Pessoa
        fields = '__all__'
