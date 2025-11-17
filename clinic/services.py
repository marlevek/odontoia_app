from django.db.models import Sum
from .models import Income, Expense 
from django.utils import timezone


# Manager do fluxo de caixa
def get_fluxo_caixa(owner, mes=None, ano=None):
    incomes = Income.objects.filter(owner = owner)
    expenses = Expense.objects.filter(owner = owner)
    
    if mes:
        incomes = incomes.filter(data__month=mes)
        expenses = expenses.filter(data__month=mes)
        
    if ano:
        incomes = incomes.filter(data__year=ano)
        expenses = expenses.filter(data__year=ano)
        
    total_receitas = incomes.aggregate(Sum('valor'))['valor__sum'] or 0
    total_despesas = expenses.aggregate(Sum('valor'))['valor__sum'] or 0
    
    saldo = total_receitas - total_despesas 
    
    return {
        'receitas': total_receitas,
        'despesas': total_despesas,
        'saldo': saldo,
    }
    
def get_graficos_financeiros(owner, ano):
    meses = list(range(1, 13))
    
    receitas_mes = []
    despesas_mes = []
    
    for mes in meses:
        total_r = Income.objects.filter(owner=owner, data__year=ano, data__month=mes).aggregate(Sum('valor'))['valor__sum'] or 0
        
        total_d = Expense.objects.filter(owner=owner, data__year=ano, data__month=mes).aggregate(Sum('valor'))['valor__sum'] or 0
        
        receitas_mes.append(float(total_r))
        despesas_mes.append(float(total_d))
        
    # Pizza de despesas por categorina no ano
    categorias = Expense.objects.filter(owner=owner, data__year=ano).values('categoria').annotate(total=Sum('valor')).order_by('-total')
    
    labels_categorias = [c['categoria'] for c in categorias]
    valores_categorias = [float(c['total']) for c in categorias]
    
    # Barras de receita por origem (manual / consulta)
    origem = Income.objects.filter(owner=owner, data__year=ano).values('origem').annotate(
        total=Sum('valor')
    )
    
    labels_receitas_origem = [o['origem'] for o in origem]
    valores_receitas_origem = [float(o['total']) for o in origem]

    return {
        "meses": meses,
        "receitas_mes": receitas_mes,
        "despesas_mes": despesas_mes,
        "labels_categorias": labels_categorias,
        "valores_categorias": valores_categorias,
        "labels_receitas_origem": labels_receitas_origem,
        "valores_receitas_origem": valores_receitas_origem,
    }