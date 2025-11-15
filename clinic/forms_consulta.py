from django import forms
from .models import Consulta, Paciente, Dentista, Procedimento


class ConsultaForm(forms.ModelForm):

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔥 Filtra tudo pelo owner
        if user:
            self.fields['paciente'].queryset = Paciente.objects.filter(owner=user)
            self.fields['dentista'].queryset = Dentista.objects.filter(owner=user)
            self.fields['procedimento'].queryset = Procedimento.objects.filter(owner=user)

        # Ajustes de estilo
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Consulta
        fields = [
            'paciente',
            'dentista',
            'procedimento',
            'data',
            'concluida',
            'paga',
            'valor',
            'desconto',
            'observacoes',
        ]

        widgets = {
            'data': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'concluida': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'paga': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
