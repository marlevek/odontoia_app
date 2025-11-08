from django import forms
from .models import Consulta


class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = ['paciente', 'dentista', 'procedimento', 'data', 'observacoes', 'concluida']
        widgets = {
            'data': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'paciente': forms.Select(attrs={'class': 'form-control'}),
            'dentista': forms.Select(attrs={'class': 'form-control'}),
            'procedimento': forms.Select(attrs={'class': 'form-control'}),
            'concluida': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
