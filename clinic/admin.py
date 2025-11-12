from django.contrib import admin
from .models import Paciente, Dentista, Consulta, Procedimento, Assinatura, Pagamento
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms


class CustomAdminSite(admin.AdminSite):
    site_header = "Odonto IA"
    site_title = "Odonto IA"
    index_title = "Dashboard - Odonto IA"
    
    class Media:
        js = ('js/admin_fix.js',)
        css = {
            'all': ('static/css/admin_custom.css',)
        }   

# usa o admin padrão
admin.site.site_header = "Odonto IA"
admin.site.site_title = "Odonto IA"
admin.site.index_title = "Dashboard - Odonto IA"


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'telefone', 'data_cadastro')
    search_fields = ('nome', 'cidade')
    list_filter = ('data_cadastro',)
    
    
@admin.register(Dentista)
class DentistaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cro', 'especialidade', 'telefone')
    search_fields = ('nome', 'cro')
    
    
@admin.register(Procedimento)
class ProcedimentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valor_base')
    search_fields = ('nome',)
    

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'dentista', 'data', 'valor_final', 'comissao_valor', 'concluida')
    list_filter = ('dentista', 'data', 'concluida')
    search_fields = ('paciente__nome', 'dentista__nome')

    fieldsets = (
        ("Informações da Consulta", {
            'fields': ('paciente', 'dentista', 'procedimento', 'data', 'concluida', 'observacoes')
        }),
        ("Financeiro", {
            'fields': ('valor', 'desconto', 'valor_final', 'comissao_valor')
        }),
    )


# --- 1️⃣ Form de criação com e-mail obrigatório e único ---
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("O e-mail é obrigatório.")

        # 🔍 Verifica duplicidade
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este e-mail já está sendo usado por outro usuário.")

        return email


# --- 2️⃣ Form de edição com e-mail obrigatório e único (exceto o próprio usuário) ---
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("O e-mail é obrigatório.")

        # Evita duplicação — ignora o próprio usuário atual
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Este e-mail já está sendo usado por outro usuário.")

        return email


# --- 3️⃣ Admin customizado ---
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    list_display = ("username", "email", "first_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")

    # Campos agrupados
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Informações pessoais", {"fields": ("first_name", "last_name", "email")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas importantes", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "first_name", "last_name", "password1", "password2"),
        }),
    )


# --- 4️⃣ Substitui o admin padrão do Django pelo customizado ---
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Assinatura)
class AssinaturaAdmin(admin.ModelAdmin):
    list_display = ("user", "ativa", "inicio_teste", "fim_teste")
    search_fields = ("user__username", "user__email")
    list_filter = ("ativa",)

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ("assinatura", "valor", "status", "metodo", "gateway", "data_criacao")
    search_fields = ("assinatura__user__username", "referencia")
    list_filter = ("status", "metodo", "gateway")
    readonly_fields = ("raw_payload",)