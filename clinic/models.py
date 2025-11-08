from django.db import models
from django.utils import timezone
from decimal import Decimal


class Paciente(models.Model):
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    email = models.EmailField()

    # Endereço (opcional)
    cep = models.CharField(max_length=9, blank=True, null=True)
    logradouro = models.CharField("Rua", max_length=150, blank=True, null=True)
    numero = models.CharField("Número", max_length=10, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField("Estado", max_length=2, blank=True, null=True)

    data_cadastro = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nome


class Dentista(models.Model):
    nome = models.CharField(max_length=100)
    cro = models.CharField(max_length=15, unique=True)
    especialidade = models.CharField(max_length=100, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, null=True)

    # 💸 Comissão automática
    comissao_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40.00,
        help_text="Percentual de comissão (%)"
    )

    def __str__(self):
        return f'{self.nome} - CRO: {self.cro}'


class Procedimento(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    valor_base = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.nome


class Consulta(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE)
    dentista = models.ForeignKey(
        'Dentista', on_delete=models.SET_NULL, null=True, blank=True)
    procedimento = models.ForeignKey('Procedimento', on_delete=models.CASCADE)
    data = models.DateTimeField()
    concluida = models.BooleanField(default=False)

    # 💰 Campos financeiros
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    desconto = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, help_text="Desconto em %")
    valor_final = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    comissao_valor = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)

    observacoes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Define valor base se estiver vazio
        if (not self.valor or self.valor == 0) and self.procedimento:
            self.valor = self.procedimento.valor_base

        # Aplica desconto
        if self.valor:
            desconto_decimal = Decimal(self.desconto or 0) / 100
            self.valor_final = self.valor * (Decimal(1) - desconto_decimal)

        # Calcula comissão
        if self.dentista and self.valor_final:
            percentual = Decimal(self.dentista.comissao_percentual or 0) / 100
            self.comissao_valor = self.valor_final * percentual
        else:
            self.comissao_valor = Decimal(0)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.paciente.nome} - {self.dentista.nome if self.dentista else 'Sem dentista'} ({self.data.strftime('%d/%m/%Y')})"
