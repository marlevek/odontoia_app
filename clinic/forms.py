from django import forms
from validate_docbr import CPF
from .models import Paciente, Procedimento, Dentista, Consulta
from django.conf import settings 
from django.core.validators import EmailValidator 
from django.core.exceptions import ValidationError


class DentistaForm(forms.ModelForm):
    class Meta:
        model = Dentista
        fields = [
            "nome",
            "cro",
            "especialidade",
            "telefone",
            "email",
            "comissao_percentual",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={'class': 'form-control'}),
            "cro": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CRO-XXX'}),
            "especialidade": forms.TextInput(attrs={'class': 'form-control'}),
            "telefone": forms.TextInput(attrs={'class': 'form-control'}),
            "email": forms.EmailInput(attrs={'class': 'form-control'}),
            "comissao_percentual": forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            EmailValidator()(email)
        return email

    def clean_comissao_percentual(self):
        valor = self.cleaned_data.get("comissao_percentual")
        if valor < 0 or valor > 100:
            raise ValidationError("A comissão deve estar entre 0% e 100%.")
        return valor

    def clean_cro(self):
        cro = self.cleaned_data.get("cro").strip().upper()

        if not cro:
            raise forms.ValidationError("O CRO é obrigatório.")

        # Validação simples (opção A)
        if len(cro) < 4:
            raise forms.ValidationError("CRO inválido.")

        return cro

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


class ConsultaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Garantir IDs e classes
        self.fields["valor"].widget.attrs.update({
            "id": "id_valor",
            "class": "form-control"
        })
        self.fields["desconto"].widget.attrs.update({
            "id": "id_desconto",
            "class": "form-control"
        })
        self.fields["procedimento"].widget.attrs.update({
            "id": "id_procedimento",
            "class": "form-select"
        })

    class Meta:
        model = Consulta
        fields = "__all__"
