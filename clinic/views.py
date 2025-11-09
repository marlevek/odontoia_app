from .models import Consulta
import re
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Paciente, Consulta, Dentista, Procedimento
from .forms import PacienteForm
from .forms_consulta import ConsultaForm
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.db.models import Count, Sum, Avg
import calendar
from datetime import timedelta
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .decorators import require_active_subscription


# === LOGIN ===
def user_login(request):
    if request.user.is_authenticated:
        return redirect('clinic:dashboard')  # se já logado, vai pro dashboard

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bem-vindo(a), {user.username}!")
                return redirect('clinic:dashboard')
            else:
                messages.error(request, "Usuário ou senha inválidos.")
        else:
            messages.error(request, "Erro ao validar o formulário.")
    else:
        form = AuthenticationForm()

    return render(request, 'clinic/login.html', {'form': form})


# === LOGOUT ===
def user_logout(request):
    logout(request)
    messages.info(request, "Você saiu do sistema com sucesso.")
    return redirect('login')


# permite AJAX sem token no protótipo (depois ajustamos segurança)
@csrf_exempt
def consulta_create_ajax(request):
    if request.method == 'POST':
        paciente_id = request.POST.get('paciente')
        dentista_id = request.POST.get('dentista')
        procedimento_id = request.POST.get('procedimento')
        data = request.POST.get('data')
        observacoes = request.POST.get('observacoes')

        try:
            data_convertida = parse_datetime(data)
            consulta = Consulta.objects.create(
                paciente_id=paciente_id,
                dentista_id=dentista_id,
                procedimento_id=procedimento_id,
                data=data_convertida,
                observacoes=observacoes,
                concluida=False
            )
            return JsonResponse({'success': True, 'id': consulta.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método inválido'})


@login_required
@require_active_subscription
def dashboard(request):
    hoje = timezone.now().date()
    periodo = int(request.GET.get('periodo', 30))  # filtro de 7 / 30 / 90 dias
    data_inicial = hoje - timedelta(days=periodo)

    # === Estatísticas gerais ===
    total_pacientes = Paciente.objects.count()
    total_consultas = Consulta.objects.count()
    consultas_concluidas = Consulta.objects.filter(concluida=True).count()
    consultas_pendentes = Consulta.objects.filter(concluida=False).count()

    # === Consultas do período ===
    consultas_periodo = Consulta.objects.filter(
        data__date__gte=data_inicial,
        data__date__lte=hoje + timedelta(days=90)
    )
    if not consultas_periodo.exists():
        consultas_periodo = Consulta.objects.all()

    # === Faturamentos ===
    faturamento_total = consultas_periodo.aggregate(
        total=Sum('valor_final')
    )['total'] or 0

    faturamento_medio = consultas_periodo.aggregate(
        media=Avg('valor_final')
    )['media'] or 0

    comissoes_total = consultas_periodo.aggregate(
        total=Sum('comissao_valor')
    )['total'] or 0

    # 💰 Faturamento líquido (total - comissões)
    faturamento_liquido = faturamento_total - comissoes_total

    # 💸 Faturamento mensal líquido
    faturamento_mensal_bruto = Consulta.objects.filter(
        data__month=hoje.month, data__year=hoje.year
    ).aggregate(total=Sum('valor_final'))['total'] or 0

    faturamento_mensal_comissoes = Consulta.objects.filter(
        data__month=hoje.month, data__year=hoje.year
    ).aggregate(total=Sum('comissao_valor'))['total'] or 0

    faturamento_mensal_liquido = faturamento_mensal_bruto - faturamento_mensal_comissoes

    # === Consultas e Receita/Comissão por dentista ===
    consultas_por_dentista = (
        consultas_periodo.exclude(dentista__isnull=True)
        .values('dentista__nome')
        .annotate(
            total_consultas=Count('id'),
            receita=Sum('valor_final'),
            comissao=Sum('comissao_valor')
        )
        .order_by('-receita')
    )

    if consultas_por_dentista:
        dentistas_labels = [c['dentista__nome'] for c in consultas_por_dentista]
        dentistas_qtd = [c['total_consultas'] for c in consultas_por_dentista]
        dentistas_receita = [float(c['receita'] or 0) for c in consultas_por_dentista]
        dentistas_comissao = [float(c['comissao'] or 0) for c in consultas_por_dentista]
    else:
        dentistas_labels = ['Sem dados']
        dentistas_qtd = [0]
        dentistas_receita = [0]
        dentistas_comissao = [0]

    # === Ranking dos dentistas ===
    ranking_dentistas = (
        consultas_periodo.values('dentista__nome')
        .annotate(
            total_consultas=Count('id'),
            receita=Sum('valor_final'),
            comissao=Sum('comissao_valor')
        )
        .order_by('-receita')[:5]
    )

    # === Consultas e Receita por mês (últimos 6 meses) ===
    meses = []
    dados_consultas = []
    dados_receita = []
    for i in range(5, -1, -1):
        mes_ref = hoje - timedelta(days=30 * i)
        nome_mes = calendar.month_abbr[mes_ref.month]
        consultas_mes = consultas_periodo.filter(
            data__month=mes_ref.month, data__year=mes_ref.year
        )
        meses.append(nome_mes)
        dados_consultas.append(consultas_mes.count())
        dados_receita.append(float(consultas_mes.aggregate(
            total=Sum('valor_final'))['total'] or 0))

    # === Status das Consultas ===
    status_consultas = {
        'concluidas': consultas_periodo.filter(concluida=True).count(),
        'pendentes': consultas_periodo.filter(concluida=False).count(),
    }

    # === Próximas Consultas ===
    inicio_semana = hoje
    fim_semana = hoje + timedelta(days=7)
    proximas_consultas = Consulta.objects.filter(
        data__date__range=[inicio_semana, fim_semana]
    ).select_related('paciente', 'dentista').order_by('data')[:8]

    # === Contexto para o template ===
    contexto = {
        'total_pacientes': total_pacientes,
        'total_consultas': total_consultas,
        'consultas_concluidas': consultas_concluidas,
        'consultas_pendentes': consultas_pendentes,
        'meses': meses,
        'dados_consultas': dados_consultas,
        'dados_receita': dados_receita,
        'proximas_consultas': proximas_consultas,
        'dentistas_labels': dentistas_labels,
        'dentistas_qtd': dentistas_qtd,
        'dentistas_receita': dentistas_receita,
        'dentistas_comissao': dentistas_comissao,
        'ranking_dentistas': ranking_dentistas,
        'periodo': periodo,

        # === Novos dados financeiros ===
        'faturamento_total': faturamento_total,
        'faturamento_liquido': faturamento_liquido,          # 👈 importante
        'faturamento_mensal': faturamento_mensal_liquido,    # 👈 líquido mensal
        'faturamento_medio': faturamento_medio,
        'comissoes_total': comissoes_total,
        'status_consultas': status_consultas,
    }

    return render(request, 'clinic/dashboard.html', contexto)


def _accent_insensitive_regex(prefix: str) -> str:
    """
    Converte 'brasilia' em uma regex que aceita acentos e casa no INÍCIO:
    '^br[aáàâã]sil[ií]a' etc. Mantém case-insensitive no __iregex.
    """
    base = {
        'a': '[aáàâã]', 'e': '[eéê]', 'i': '[ií]', 'o': '[oóôõ]', 'u': '[uú]',
        'c': '[cç]'
    }
    # escapa tudo e depois troca letras por classes
    esc = re.escape(prefix.strip().lower())
    # aplica mapeamento
    pattern = ''
    for ch in esc:
        pattern += base.get(ch, ch)
    return '^' + pattern  # começa com



def pacientes_list(request):
    search = (request.GET.get('search') or '').strip()
    pacientes = Paciente.objects.all().order_by('-data_cadastro')

    if search:
        regex = _accent_insensitive_regex(search)
        pacientes = pacientes.filter(
            Q(nome__iregex=regex) | Q(cidade__iregex=regex)
        )

    context = {
        'pacientes': pacientes,
        'search': search,
    }
    return render(request, 'clinic/pacientes_list.html', context)



def paciente_create(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Paciente cadastrado com sucesso!")
            return redirect('clinic:pacientes_list')
        else:
            messages.error(
                request, "⚠️ Corrija os erros abaixo antes de salvar.")
    else:
        form = PacienteForm()

    return render(request, 'clinic/paciente_form.html', {'form': form, 'titulo': 'Novo Paciente'})



def paciente_update(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, "Dados do paciente atualizados!")
            return redirect('clinic:pacientes_list')
    else:
        form = PacienteForm(instance=paciente)
    return render(request, 'clinic/paciente_form.html', {'form': form, 'titulo': 'Editar Paciente'})


def paciente_delete(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        paciente.delete()
        messages.success(request, "Paciente excluído com sucesso.")
        return redirect('clinic:pacientes_list')
    return render(request, 'clinic/paciente_confirm_delete.html', {'paciente': paciente})



def consultas_list(request):
    # Obter filtros via GET
    search = request.GET.get('search')
    status = request.GET.get('status')
    data_filtro = request.GET.get('data')

    consultas = Consulta.objects.select_related(
        'paciente', 'dentista', 'procedimento').order_by('-data')

    # 🔍 Filtro por nome do paciente ou dentista
    if search:
        consultas = consultas.filter(
            Q(paciente__nome__icontains=search) |
            Q(dentista__nome__icontains=search)
        )

    # ✅ Filtro por status
    if status == 'pendente':
        consultas = consultas.filter(concluida=False)
    elif status == 'concluida':
        consultas = consultas.filter(concluida=True)

    # 📅 Filtro por data específica
    if data_filtro:
        try:
            data_convertida = parse_date(data_filtro)
            if data_convertida:
                consultas = consultas.filter(data__date=data_convertida)
        except Exception:
            pass

    context = {
        'consultas': consultas,
        'search': search or '',
        'status': status or '',
        'data_filtro': data_filtro or '',
    }
    return render(request, 'clinic/consultas_list.html', context)


def consulta_update(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)

    if request.method == 'POST':
        form = ConsultaForm(request.POST, instance=consulta)
        if form.is_valid():
            form.save()
            return redirect('clinic:consultas_list')
    else:
        form = ConsultaForm(instance=consulta)

    return render(request, 'clinic/consulta_form.html', {'form': form, 'consulta': consulta})


def consulta_create(request):
    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Consulta agendada com sucesso!")
            return redirect('clinic:consultas_list')
        else:
            messages.error(
                request, "⚠️ Corrija os erros abaixo antes de salvar.")
    else:
        form = ConsultaForm()
    return render(request, 'clinic/consulta_form.html', {'form': form, 'titulo': 'Nova Consulta'})


@csrf_exempt
def consulta_update_ajax(request):
    if request.method == "POST":
        consulta_id = request.POST.get("id")
        nova_data = request.POST.get("start")

        try:
            consulta = Consulta.objects.get(pk=consulta_id)
            data_convertida = parse_datetime(nova_data)
            if data_convertida:
                consulta.data = data_convertida
                consulta.save()
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "Data inválida"})
        except Consulta.DoesNotExist:
            return JsonResponse({"success": False, "error": "Consulta não encontrada"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método inválido"})


def consulta_delete(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)
    if request.method == 'POST':
        consulta.delete()
        messages.success(request, "Consulta excluída com sucesso.")
        return redirect('clinic:consultas_list')
    return render(request, 'clinic/consulta_confirm_delete.html', {'consulta': consulta})



def consultas_calendar(request):
    # 🔍 Se for uma chamada AJAX do FullCalendar (com 'start' e 'end')
    if request.GET.get('start') and request.GET.get('end'):
        dentista_id = request.GET.get('dentista')
        consultas = Consulta.objects.select_related(
            'paciente', 'dentista', 'procedimento').all()

        if dentista_id:
            consultas = consultas.filter(dentista_id=dentista_id)

        events = []
        for consulta in consultas:
            color = "#0b5394" if not consulta.concluida else "#28a745"
            events.append({
                "id": consulta.id,
                "title": f"{consulta.paciente.nome}",
                "start": consulta.data.isoformat(),
                "backgroundColor": color,
                "borderColor": color,
                "textColor": "white",
                "extendedProps": {
                    "dentista": consulta.dentista.nome if consulta.dentista else "",
                    "procedimento": consulta.procedimento.nome if consulta.procedimento else "",
                    "observacoes": consulta.observacoes or ""
                },
                "url": f"/consultas/{consulta.id}/editar/"
            })
        return JsonResponse(events, safe=False)

    # 👇 Renderiza o template normal
    return render(request, 'clinic/consultas_calendar.html', {
        'pacientes': Paciente.objects.all(),
        'dentistas': Dentista.objects.all(),
        'procedimentos': Procedimento.objects.all(),
    })

    # Se não for chamada com start/end → renderiza o template normal
    return render(request, 'clinic/consultas_calendar.html')


def dashboard_data(request):
    hoje = timezone.now().date()
    periodo = int(request.GET.get('periodo', 30))
    data_inicial = hoje - timedelta(days=periodo)

    # 🔍 Consultas dentro do período selecionado
    consultas_periodo = Consulta.objects.filter(
        data__date__gte=data_inicial,
        data__date__lte=hoje + timedelta(days=90)
    )

    # 💰 Faturamento total (somatório de todos os valores finais)
    faturamento_total = consultas_periodo.aggregate(
        total=Sum('valor_final')
    )['total'] or 0

    # 💳 Ticket médio (média dos valores finais)
    faturamento_medio = consultas_periodo.aggregate(
        media=Avg('valor_final')
    )['media'] or 0

    # 💸 Total de comissões
    comissoes_total = consultas_periodo.aggregate(
        total=Sum('comissao_valor')
    )['total'] or 0

    # 🧾 Faturamento líquido = total - comissões
    faturamento_liquido = faturamento_total - comissoes_total

    # 🗓️ Faturamento mensal (mês corrente)
    faturamento_mensal_bruto = Consulta.objects.filter(
        data__month=hoje.month, data__year=hoje.year
    ).aggregate(total=Sum('valor_final'))['total'] or 0

    faturamento_mensal_comissoes = Consulta.objects.filter(
        data__month=hoje.month, data__year=hoje.year
    ).aggregate(total=Sum('comissao_valor'))['total'] or 0

    faturamento_mensal_liquido = faturamento_mensal_bruto - faturamento_mensal_comissoes

    # 📊 Status das consultas
    status_consultas = {
        'concluidas': consultas_periodo.filter(concluida=True).count(),
        'pendentes': consultas_periodo.filter(concluida=False).count(),
    }

    # 🦷 Consultas e receita por dentista
    consultas_por_dentista = (
        consultas_periodo.exclude(dentista__isnull=True)
        .values('dentista__nome')
        .annotate(
            total_consultas=Count('id'),
            receita=Sum('valor_final'),
            comissao=Sum('comissao_valor')
        )
        .order_by('-receita')
    )

    # 📅 Gráficos mensais (últimos 6 meses)
    meses = []
    dados_consultas = []
    dados_receita = []

    for i in range(5, -1, -1):
        mes_ref = hoje - timedelta(days=30 * i)
        nome_mes = calendar.month_abbr[mes_ref.month]
        consultas_mes = consultas_periodo.filter(
            data__month=mes_ref.month, data__year=mes_ref.year
        )
        meses.append(nome_mes)
        dados_consultas.append(consultas_mes.count())
        dados_receita.append(float(
            consultas_mes.aggregate(total=Sum('valor_final'))['total'] or 0
        ))

    # 📦 Retorno dos dados
    data = {
        'faturamento_total': float(faturamento_total),
        'faturamento_liquido': float(faturamento_liquido),
        'faturamento_mensal': float(faturamento_mensal_liquido),
        'faturamento_medio': float(faturamento_medio),
        'comissoes_total': float(comissoes_total),
        'status_consultas': status_consultas,
        'dentistas': list(consultas_por_dentista),
        'meses': meses,
        'dados_consultas': dados_consultas,
        'dados_receita': dados_receita,
    }

    return JsonResponse(data)


@csrf_exempt
def consulta_create_ajax(request):
    if request.method == "POST":
        try:
            paciente_id = request.POST.get("paciente")
            dentista_id = request.POST.get("dentista")
            procedimento_id = request.POST.get("procedimento")
            data = request.POST.get("data")
            observacoes = request.POST.get("observacoes", "")

            consulta = Consulta.objects.create(
                paciente_id=paciente_id,
                dentista_id=dentista_id,
                procedimento_id=procedimento_id,
                data=data,
                observacoes=observacoes,
            )
            return JsonResponse({"success": True, "id": consulta.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método inválido"})


def registrar_teste(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Usuário já existe.")
            return redirect('registrar_teste')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.date_joined = timezone.now()
        user.save()

        # Define uma data de expiração do teste
        request.session['trial_expires'] = (timezone.now() + timedelta(days=7)).isoformat()
        messages.success(request, "Conta de teste criada com sucesso! Aproveite seus 7 dias gratuitos.")
        return redirect('clinic:dashboard')

    return render(request, 'clinic/registrar_teste.html')