from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import ClinicaConfig, Assinatura

@receiver(post_save, sender=Assinatura)
def criar_config_clinica(sender, instance, created, **kwargs):
    """
    Quando o usuário vira premium → cria a configuração da clínica.
    """
    if instance.tipo == "premium" and instance.ativa:
        ClinicaConfig.objects.get_or_create(user=instance.user)
