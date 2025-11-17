from django import forms
from validate_docbr import CPF
from .models import Paciente, Procedimento, Dentista, Consulta, Income, Expense
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
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtra os querysets pelo usuário logado
        if user:
            self.fields['paciente'].queryset = Paciente.objects.filter(owner=user)
            self.fields['dentista'].queryset = Dentista.objects.filter(owner=user)
            self.fields['procedimento'].queryset = Procedimento.objects.filter(owner=user)

    class Meta:
        model = Consulta
        fields = '__all__'
        widgets = {
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_valor',
                'step': '0.01',
                'placeholder': '0,00'
            }),
            'desconto': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_desconto', 
                'step': '0.01',
                'placeholder': '0,00'
            }),
            'paciente': forms.Select(attrs={'class': 'form-select'}),
            'dentista': forms.Select(attrs={'class': 'form-select'}),
            'procedimento': forms.Select(attrs={
                'class': 'form-select', 
                'id': 'id_procedimento'
            }),
            'data': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'autocomplete': 'off'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'concluida': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'paga': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Se um procedimento foi selecionado, usa o valor_base automaticamente
        if instance.procedimento and (not instance.valor or instance.valor == 0):
            instance.valor = instance.procedimento.valor_base
            
        if commit:
            instance.save()
            self.save_m2m()
            
        return instance
    
    
class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income 
        fields = ['descricao', 'valor', 'data', 'pago']
        widgets ={
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pago': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['categoria', 'descricao', 'valor', 'data', 'pago']
        widgets = {
            'categoria': forms.TextInput(attrs={'class':'form-control'}),
            'descricao': forms.TextInput(attrs={'class':'form-control'}),
            'valor': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'data': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'pago': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }