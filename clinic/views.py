from .models import Consulta
from .utils.contexto_dinamico import gerar_contexto_dinamico
import re
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Paciente, Consulta, Dentista, Procedimento, Assinatura, Pagamento
from .forms import PacienteForm, ProcedimentoForm
from .forms_consulta import ConsultaForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
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
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from openai import OpenAI
import json
import os
import uuid
import mercadopago
from decimal import Decimal
from django.urls import reverse


# inicializa o client globalmente mas de forma segura
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _odontoia_system_prompt(user):
    from .utils.contexto_dinamico import gerar_contexto_dinamico

    nome = user.first_name or user.username
    contexto_dinamico = gerar_contexto_dinamico(user)

    return f"""
Você é o **Assistente Oficial do OdontoIA**, um sistema de gestão odontológica voltado a dentistas, clínicas e secretárias.

Regras fundamentais:
- Sempre responda em **português (pt-BR)**, de forma profissional, breve e empática.
- **Nunca forneça informações clínicas** sobre pacientes, diagnósticos ou tratamentos odontológicos.
- O foco é **ensinar o usuário a usar o sistema OdontoIA**.
- O público-alvo são **usuários do sistema (dentistas, secretárias, administradores)**, não pacientes.
- Se o usuário perguntar “como faço X”, explique o caminho pelo sistema (menus e páginas) de forma prática.
- Use os nomes exatos dos menus do OdontoIA: **Dashboard**, **Pacientes**, **Consultas**, **Procedimentos**, **Agenda**, **Financeiro**, **/admin** (apenas administradores).

Contexto real do sistema:
- O cadastro de **dentistas** é feito **somente por usuários administradores**, no painel **/admin**, usando o campo **CRO**.
- O cadastro de **pacientes** e **procedimentos** é feito diretamente no app.
- O módulo de **consultas** permite marcar, editar e concluir atendimentos.
- O módulo de **financeiro** mostra comissões, faturamento e lucro líquido.
- O sistema possui **teste gratuito de 7 dias**, após o qual a conta precisa de assinatura ativa.
- Se o usuário perguntar sobre **planos ou preços**, explique que há planos **Básico**, **Profissional** e **Premium**.
- Se o trial estiver próximo de expirar, lembre da página de planos (https://odontoia.codertec.com.br).

Comportamento:
- Seja proativo e claro (ex: “Vá até ‘Pacientes’ > ‘Novo Paciente’”).
- Se a ação for restrita (como cadastrar dentista), avise que só **administradores** podem fazer.
- Se não souber, oriente a procurar o suporte da Codertec.

📊 **Dados em tempo real do sistema:**
{contexto_dinamico}

Contexto atual:
- Usuário logado: {nome}
- Data e hora: {timezone.now().strftime('%d/%m/%Y %H:%M')}
    """.strip()


def _get_openai_client():
    try:
        from openai import OpenAI
    except Exception as e:
        return None, f"SDK OpenAI não disponível: {e}"

    # tenta .env → settings
    api_key = os.getenv("OPENAI_API_KEY") or getattr(
        settings, "OPENAI_API_KEY", None)
    if not api_key:
        return None, "OPENAI_API_KEY não configurada (adicione no .env ou nas variáveis do serviço)."

    try:
        client = OpenAI(api_key=api_key)  # sem proxies/kwargs estranhos
        return client, None
    except Exception as e:
        return None, f"Falha ao criar cliente OpenAI: {e}"

# ── Endpoint de diagnóstico (opcional, ajuda no debug) ─────────────────────


@csrf_exempt
@login_required
@require_GET
def chat_diag(request):
    has_key = bool(os.getenv("OPENAI_API_KEY") or getattr(
        settings, "OPENAI_API_KEY", None))
    return JsonResponse({
        "ok": True,
        "user": request.user.username,
        "openai_key_present": has_key,
    })


# ── Endpoint principal do chat ──────────────────────────────────────────────
@csrf_exempt                 # evita dor de cabeça com CSRF no fetch
@login_required              # exige login (se 302 → login)
@require_POST
def chat_odontoia_api(request):
    # lê payload
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        user_msg = (payload.get("message") or "").strip()
    except Exception:
        return JsonResponse({"error": "Payload inválido."}, status=400)

    if not user_msg:
        return JsonResponse({"error": "Mensagem vazia."}, status=400)

    # cliente OpenAI
    client, err = _get_openai_client()
    if err:
        # devolve o motivo real pro front (facilita corrigir config)
        return JsonResponse({"error": err}, status=500)

    # histórico (curto) na sessão
    history = request.session.get("chat_history", [])
    messages = [
        {"role": "system", "content": _odontoia_system_prompt(request.user)}]
    messages.extend(history[-20:])  # últimos turnos
    messages.append({"role": "user", "content": user_msg})

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
        )
        answer = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        # log no servidor e motivo no front
        print("OpenAI error:", repr(e))
        return JsonResponse({"error": f"OpenAI falhou: {e}"}, status=502)

    # salva histórico
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": answer})
    request.session["chat_history"] = history

    return JsonResponse({"answer": answer})


# === LOGIN ===
def user_login(request):
    if request.user.is_authenticated:
        return redirect('clinic:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                # 🔄 limpa mensagens anteriores
                storage = messages.get_messages(request)
                for _ in storage:
                    pass

                messages.success(request, f"Bem-vindo(a), {user.username}!")

                # Se ainda não viu a tela de boas vindas
                if not request.session.get('onboarding_done', False):
                    return redirect('clinic:onboarding')

                # Caso contrário vai para dashboard
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
    """
    Faz logout, limpa mensagens antigas e redireciona para login sem conflito.
    """
    logout(request)

    # ⚙️ Limpa mensagens antigas antes de adicionar uma nova
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # força limpeza

    messages.success(request, "Você saiu do sistema com sucesso.")
    return redirect("clinic:login")


# permite AJAX sem token no protótipo (depois ajustamos segurança)
@csrf_exempt
@login_required
@require_active_subscription
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
        dentistas_labels = [c['dentista__nome']
                            for c in consultas_por_dentista]
        dentistas_qtd = [c['total_consultas'] for c in consultas_por_dentista]
        dentistas_receita = [float(c['receita'] or 0)
                             for c in consultas_por_dentista]
        dentistas_comissao = [float(c['comissao'] or 0)
                              for c in consultas_por_dentista]
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
    
    # === Assinatura e plano atual ===
    assinatura = Assinatura.objects.filter(user=request.user).first()
    ultimo_pgto = (
        Pagamento.objects.filter(assinatura=assinatura, status='pago')
        .order_by('-data_pagamento')
        .first()
        if assinatura else None
    )
    
    # Inicializa as variáveis de forma segura
    plano_atual = None
    validade = None
    
    if assinatura:
        validade = assinatura.fim_teste
        if ultimo_pgto:
            # Se o modelo Pagamento tiver camplo 'plano'
            plano_atual = getattr(ultimo_pgto, 'plano', None) or 'Assinatura Ativa'
        elif assinatura.ativa:
            # Pode estar ativo mas sem pagamento registrado (ex: trial)
            plano_atual = getattr(assinatura, 'tipo', None) or 'Trial'
    
    # --- adiciona essas variáveis ao contexto ---
    contexto.update({
        'plano_atual': plano_atual,
        'validade': validade,
    })
    
               
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


@login_required
@require_active_subscription
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


@login_required
@require_active_subscription
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


@login_required
@require_active_subscription
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


@login_required
@require_active_subscription
def paciente_delete(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        paciente.delete()
        messages.success(request, "Paciente excluído com sucesso.")
        return redirect('clinic:pacientes_list')
    return render(request, 'clinic/paciente_confirm_delete.html', {'paciente': paciente})


@login_required
@require_active_subscription
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


@login_required
@require_active_subscription
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


@login_required
@require_active_subscription
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


@login_required
@require_active_subscription
def consulta_delete(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)
    if request.method == 'POST':
        consulta.delete()
        messages.success(request, "Consulta excluída com sucesso.")
        return redirect('clinic:consultas_list')
    return render(request, 'clinic/consulta_confirm_delete.html', {'consulta': consulta})


@login_required
@require_active_subscription
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
@login_required
@require_active_subscription
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

        # Verifica se o nome de usuário já existe
        if User.objects.filter(username=username).exists():
            messages.error(request, "Usuário já existe.")
            return redirect('clinic:registrar_teste')

        # Verifica se o e-mail foi informado
        if not email:
            messages.error(
                request, "O e-mail é obrigatório para criar uma conta.")
            # 👈 aqui ajustei o namespace
            return redirect('clinic:registrar_teste')

        # Cria o usuário
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.date_joined = timezone.now()
        user.save()

        # Cria assinatura trial automaticamente
        Assinatura.objects.create(user=user, tipo='trial')

        # Faz login automático após criar conta
        login(request, user)

        messages.success(
            request,
            f"Conta de teste criada com sucesso! Bem-vindo(a), {user.username}.Aproveite seus 7 dias gratuitos."
        )
        return redirect('clinic:onboarding')

    # GET → renderiza o formulário normalmente
    return render(request, 'clinic/registrar_teste.html')


@login_required
@require_active_subscription
def procedimentos_list(request):
    procedimentos = Procedimento.objects.all().order_by('nome')
    return render(request, 'clinic/procedimentos_list.html', {'procedimentos': procedimentos})


@login_required
@require_active_subscription
def procedimento_create(request):
    if request.method == 'POST':
        form = ProcedimentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clinic:procedimentos_list')
    else:
        form = ProcedimentoForm()
    return render(request, 'clinic/procedimento_form.html', {'form': form, 'titulo': 'Novo Procedimento'})


@login_required
@require_active_subscription
def procedimento_edit(request, id):
    procedimento = get_object_or_404(Procedimento, id=id)
    if request.method == 'POST':
        form = ProcedimentoForm(request.POST, instance=procedimento)
        if form.is_valid():
            form.save()
            return redirect('clinic:procedimentos_list')
    else:
        form = ProcedimentoForm(instance=procedimento)
    return render(request, 'clinic/procedimento_form.html', {'form': form, 'titulo': 'Editar Procedimento'})


def assinatura_expirada(request):
    return render(request, "clinic/assinatura_expirada.html")


@csrf_exempt
def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        if not email:
            messages.error(request, "Por favor, informe um e-mail válido.")
            return redirect("login")

        # Verifica se há um usuário com este e-mail
        user = User.objects.filter(email=email).first()
        if not user:
            messages.warning(
                request, "E-mail não encontrado. Verifique ou entre em contato com o suporte.")
            return redirect("login")

        # Simulação de envio de e-mail (você pode configurar SMTP real)
        assunto = "Recuperação de acesso - OdontoIA"
        corpo = f"""
Olá, {user.username}!

Recebemos uma solicitação para recuperar o acesso ao OdontoIA.

Usuário: {user.username}
Se esqueceu sua senha, redefina acessando: https://odontoia.codertec.com.br/resetar-senha/

Atenciosamente,
Equipe OdontoIA
        """
        try:
            send_mail(
                assunto,
                corpo,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(
                request, "E-mail enviado com sucesso! Verifique sua caixa de entrada.")
        except Exception as e:
            print("Erro ao enviar e-mail:", e)
            messages.error(
                request, "Não foi possível enviar o e-mail. Tente novamente mais tarde.")

        return redirect("login")

    return redirect("login")


# ===============================
# 💌 Recuperação de Senha (HTML)
# ===============================
@csrf_exempt
def password_reset_request(request):
    """
    Exibe modal e envia e-mail estilizado com link de redefinição de senha.
    """
    if request.method == "POST":
        email = request.POST.get("email")
        if not email:
            return JsonResponse({"success": False, "error": "Informe o e-mail de cadastro."})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({"success": False, "error": "E-mail não encontrado no sistema."})

        # Gera token de redefinição
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = request.build_absolute_uri(f"/reset/{uid}/{token}/")

        # Renderiza template HTML do e-mail
        context = {
            "user": user,
            "reset_url": reset_url,
        }
        html_content = render_to_string(
            "clinic/emails/password_reset_email.html", context)
        subject = "🔑 Redefinição de senha - OdontoIA"

        msg = EmailMultiAlternatives(
            subject,
            f"Olá {user.username},\n\nPara redefinir sua senha, acesse o link abaixo:\n{reset_url}\n\nEquipe OdontoIA",
            "OdontoIA <no-reply@odontoia.com.br>",
            [email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Método inválido."})


@login_required
def onboarding(request):
    """
    Mostra uma tela de boas-vindas e primeiros passos para novos usuários.
    Só aparece uma vez por usuário.
    """
    if request.session.get('onboarding_done'):
        return redirect('clinic:dashboard')

    assinatura = Assinatura.objects.filter(user=request.user).first()
    tipo_assinatura = assinatura.tipo if assinatura else 'trial'

    if request.method == 'POST':
        request.session['onboarding_done'] = True
        return redirect('clinic:dashboard')

    return render(request, 'clinic/onboarding.html')


# ==== PAGAMENTOS (Mercado Pago) ============================================

def _get_mp_sdk():
    """
    Retorna o SDK autenticado do Mercado Pago, ou lança erro amigável se faltar token.
    """
    import mercadopago
    from django.conf import settings

    access_token = getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", None)
    if not access_token:
        print("❌ Falha: variável MERCADOPAGO_ACCESS_TOKEN ausente no settings.")
        raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN não configurado.")

    try:
        return mercadopago.SDK(access_token)
    except Exception as e:
        print(f"❌ Erro ao inicializar SDK do Mercado Pago: {e}")
        raise


PLANOS = {
    "basico": Decimal("49.90"),
    "profissional": Decimal("79.90"),
    "premium": Decimal("129.90"),
}


@login_required
def criar_pagamento(request, plano: str):
    """
    Cria uma Preference no Mercado Pago e redireciona o usuário ao checkout.
    """
    plano = plano.lower().strip()
    if plano not in PLANOS:
        messages.error(request, "Plano inválido.")
        return redirect("clinic:dashboard")

    valor = PLANOS[plano]
    assinatura, _ = Assinatura.objects.get_or_create(user=request.user)

    referencia = f"odontoia-{request.user.id}-{uuid.uuid4().hex}"

    pagamento = Pagamento.objects.create(
        assinatura=assinatura,
        referencia=referencia,
        valor=valor,
        status="pendente",
        metodo="desconhecido",
        plano=plano.capitalize(),  # ✅ salva o nome do plano direto no modelo
    )

    sdk = _get_mp_sdk()

    success_url = request.build_absolute_uri(reverse("clinic:pagamento_sucesso"))
    failure_url = request.build_absolute_uri(reverse("clinic:pagamento_falha"))
    webhook_url = request.build_absolute_uri(reverse("clinic:mercadopago_webhook"))

    try:
        preference_data = {
            "items": [
                {
                    "id": referencia,
                    "title": f"Plano {plano.capitalize()} - OdontoIA",
                    "description": "Assinatura OdontoIA",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": float(valor),
                }
            ],
            "payer": {"email": request.user.email or "sem-email@odontoia.local"},
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": success_url,
            },
            "external_reference": referencia,
        }

        # ⚙️ notification_url apenas em produção
        if not settings.DEBUG:
            preference_data["notification_url"] = webhook_url

        print("📦 Enviando preference_data:", json.dumps(preference_data, indent=2, ensure_ascii=False))

        pref = sdk.preference().create(preference_data)
        resp = pref.get("response", {})
        init_point = resp.get("init_point") or resp.get("sandbox_init_point")

        if not init_point:
            msg = resp.get("message", "resposta inválida do Mercado Pago")
            messages.error(request, f"Falha ao iniciar checkout: {msg}")
            print("⚠️ init_point ausente - resposta:", resp)
            return redirect("clinic:dashboard")

        return redirect(init_point)

    except Exception as e:
        import traceback
        print("❌ ERRO ao criar preferência no Mercado Pago:")
        traceback.print_exc()
        messages.error(request, f"Falha ao iniciar checkout no Mercado Pago: {e}")
        return redirect("clinic:dashboard")


# ===========================
# 🧾 WEBHOOK DO MERCADO PAGO
# ===========================
@csrf_exempt
def mercadopago_webhook(request):
    """
    Recebe notificações automáticas do Mercado Pago sobre pagamentos.
    """
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    payment_id = payload.get("data", {}).get("id") or payload.get("id")
    if not payment_id:
        return JsonResponse({"ok": True, "ignored": True})

    sdk = _get_mp_sdk()
    payment_info = sdk.payment().get(payment_id).get("response", {})

    status = payment_info.get("status")
    external_reference = payment_info.get("external_reference")
    payment_method = (payment_info.get("payment_method_id") or "desconhecido").lower()

    if not external_reference:
        return JsonResponse({"ok": True, "missing_external_reference": True})

    pgto = Pagamento.objects.filter(referencia=external_reference).first()
    if not pgto:
        return JsonResponse({"ok": True, "unknown_reference": True})

    pgto.raw_payload = payload
    pgto.metodo = (
        "pix" if "pix" in payment_method
        else "card" if any(k in payment_method for k in ["visa", "master", "amex", "hiper", "elo"])
        else "boleto" if "boleto" in payment_method
        else "desconhecido"
    )

    if status == "approved":
        pgto.status = "pago"
        pgto.data_pagamento = timezone.now()
        pgto.save()

        assinatura = pgto.assinatura
        assinatura.ativa = True
        assinatura.fim_teste = timezone.now() + timezone.timedelta(days=30)
        assinatura.save()
    elif status in ("rejected", "cancelled", "refunded", "charged_back"):
        pgto.status = "falhou"
        pgto.save()
    else:
        pgto.status = "pendente"
        pgto.save()

    return JsonResponse({"ok": True})


# ===========================
# ✅ PÁGINA DE SUCESSO
# ===========================
@login_required
def pagamento_sucesso(request):
    assinatura = Assinatura.objects.filter(user=request.user).first()
    pagamento = (
        Pagamento.objects.filter(assinatura__user=request.user)
        .order_by("-data_pagamento")
        .first()
    )

    if not assinatura or not pagamento:
        messages.warning(request, "Não foi possível carregar os dados do pagamento.")
        return redirect("clinic:dashboard")

    return render(
        request,
        "clinic/pagamento_sucesso.html",
        {"assinatura": assinatura, "pagamento": pagamento, "plano": pagamento.plano},
    )


# ===========================
# ❌ PÁGINA DE FALHA
# ===========================
@login_required
def pagamento_falha(request):
    pagamento = (
        Pagamento.objects.filter(assinatura__user=request.user)
        .order_by("-data_pagamento")
        .first()
    )

    plano = pagamento.plano if pagamento else "Indefinido"

    return render(request, "clinic/pagamento_falha.html", {"plano": plano})
