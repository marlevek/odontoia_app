from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


def default_fim_teste():
    """Define a data padrão de fim do teste (7 dias após o início)."""
    return timezone.now() + timedelta(days=7)


class Assinatura(models.Model):
    PLANOS = [
        ("trial", "Teste Gratuito"),
        ("basico", "Plano Básico"),
        ("profissional", "Plano Profissional"),
        ("premium", "Plano Premium"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=PLANOS, default="trial")
    inicio_teste = models.DateTimeField(default=timezone.now)
    fim_teste = models.DateTimeField(default=default_fim_teste)
    ativa = models.BooleanField(default=True)

    def dias_restantes(self):
        """Calcula quantos dias faltam até o fim do teste ou plano."""
        if not self.fim_teste:
            return 0
        diff = (self.fim_teste - timezone.now()).days
        return max(diff, 0)

    def expirou(self):
        """Retorna True se a assinatura expirou."""
        return timezone.now() > self.fim_teste

    def esta_no_trial(self):
        """Verifica se é um plano de teste gratuito."""
        return self.tipo == "trial"

    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_display()} ({'Ativa' if self.ativa else 'Inativa'})"


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
    nome = models.CharField(max_length=255)
    valor_base = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nome} - R$ {self.valor_base}"


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


class Pagamento(models.Model):
    """
    Registra transações de pagamento vinculadas a uma Assinatura.
    """
    METODOS = (
        ("pix", "PIX"),
        ("card", "Cartão"),
        ("boleto", "Boleto"),
        ("desconhecido", "Desconhecido"),
    )
    STATUS = (
        ("pendente", "Pendente"),
        ("pago", "Pago"),
        ("falhou", "Falhou"),
        ("cancelado", "Cancelado"),
    )
    plano = models.CharField(max_length=50, default='Indefinido')
    assinatura = models.ForeignKey('Assinatura', on_delete=models.CASCADE, related_name='pagamentos')
    referencia = models.CharField(max_length=150, unique=True)  # usamos como external_reference
    gateway = models.CharField(max_length=50, default="mercadopago")
    metodo = models.CharField(max_length=20, choices=METODOS, default="desconhecido")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_pagamento = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField(null=True, blank=True)  # opcional: último payload do MP

    def __str__(self):
        return f"{self.assinatura.user.username} - {self.status} - {self.valor}"
    
