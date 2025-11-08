from django.contrib import admin
from .models import Paciente, Dentista, Consulta, Procedimento


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
