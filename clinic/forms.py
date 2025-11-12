from django import forms
from validate_docbr import CPF
from .models import Paciente, Procedimento
from django.conf import settings 


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nome', 'cpf', 'data_nascimento', 'telefone', 'email',
            'cep', 'logradouro', 'numero', 'bairro', 'cidade', 'uf'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control cpf', 'placeholder': '000.000.000-00'}),
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control telefone', 'placeholder': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control cep', 'placeholder': '00000-000'}),
            'logradouro': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'uf': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_cpf(self):
        cpf_value = self.cleaned_data.get('cpf')

        if not cpf_value:
            raise forms.ValidationError("O CPF é obrigatório.")

        cpf_value = cpf_value.replace('.', '').replace('-', '').strip()

        # Se o ambiente está em modo DEBUG, aceitar CPFs fictícios
        if settings.DEBUG:
            # Permite CPFs com todos os dígitos iguais (ex: 111.111.111-11) ou aleatórios
            return cpf_value

        # Em produção, validar rigorosamente
        cpf_validator = CPF()
        if not cpf_validator.validate(cpf_value):
            raise forms.ValidationError("CPF inválido. Verifique os dígitos.")
        
        return cpf_value


class ProcedimentoForm(forms.ModelForm):
    class Meta:
        model = Procedimento
        fields = ['nome', 'descricao', 'valor_base']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'valor_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),   
            }