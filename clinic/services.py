from django.db.models import Sum
from .models import Income, Expense 


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