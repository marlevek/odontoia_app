# clinic/utils/subscription.py
from datetime import timedelta
from django.utils import timezone

TRIAL_DAYS = 7
NEAR_EXPIRY_THRESHOLD = 3  # dias

def get_trial_end_for_user(user):
    """
    Tenta ler trial_end de algum lugar (User.profile.trial_end, User.trial_end, etc).
    Se não existir, calcula como date_joined + TRIAL_DAYS.
    Ajuste aqui caso você já tenha Subscription/Clinic com campo trial_end.
    """
    # 1) user.profile.trial_end
    trial_end = getattr(getattr(user, "profile", None), "trial_end", None)
    # 2) user.trial_end (se houver no model do User)
    if trial_end is None:
        trial_end = getattr(user, "trial_end", None)
    # 3) fallback: date_joined + TRIAL_DAYS
    if trial_end is None:
        trial_end = user.date_joined + timedelta(days=TRIAL_DAYS)
    return trial_end

def get_trial_info(user):
    """
    Retorna um dicionário com status do teste.
    """
    now = timezone.now()
    trial_end = get_trial_end_for_user(user)
    # compara por data (ignora hora)
    days_left = (trial_end.date() - now.date()).days
    status = "active" if days_left >= 0 else "expired"
    near_expiry = (0 <= days_left <= NEAR_EXPIRY_THRESHOLD)
    return {
        "end": trial_end,
        "days_left": max(days_left, 0),
        "raw_days_left": days_left,  # útil pra lógicas finas
        "status": status,
        "near_expiry": near_expiry,
        "threshold": NEAR_EXPIRY_THRESHOLD,
    }
