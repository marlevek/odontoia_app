# clinic/context_processors.py
from .utils.subscription import get_trial_info

def trial_status(request):
    if not request.user.is_authenticated:
        return {}
    info = get_trial_info(request.user)
    return {"trial": info}
