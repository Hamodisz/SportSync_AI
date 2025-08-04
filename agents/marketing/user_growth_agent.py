# agents/marketing/user_growth_agent.py

from analysis.analysis_layers_1_40 import apply_layers_1_40
from analysis.analysis_layers_41_80 import apply_layers_41_80
from analysis.analysis_layers_81_100 import apply_layers_81_100
from analysis.analysis_layers_101_141 import apply_layers_101_141
from analysis.layer_z_engine import analyze_silent_drivers
from analysis.user_analysis import summarize_traits
from core.user_logger import log_user_insight
from data.insights_log import load_insights
import datetime

def optimize_growth_strategy(user_data, platform="youtube", lang="en"):
    """
    يولّد إستراتيجية نمو ذكية بناءً على الطبقات التحليلية والسلوك العميق
    """
    traits_1_40   = apply_layers_1_40(user_data)
    traits_41_80  = apply_layers_41_80(user_data)
    traits_81_100 = apply_layers_81_100(user_data)
    traits_101_141= apply_layers_101_141(user_data)
    silent_drivers= analyze_silent_drivers(user_data)

    summary = summarize_traits({
        **traits_1_40,
        **traits_41_80,
        **traits_81_100,
        **traits_101_141,
        **silent_drivers
    })

    # تحديد أوقات النشر المثالية
    timing = "evening" if summary.get("energy_pattern") == "night" else "morning"

    # تحديد المنصة المناسبة
    best_platform = platform if summary.get("preferred_content") == "video" else "instagram"

    # تحديد نوع الحملة (تعليمية/عاطفية/ترند)
    if summary.get("core_emotion") == "inspiration":
        campaign_type = "emotional viral boost"
    elif summary.get("core_motivation") == "mastery":
        campaign_type = "educational challenge series"
    else:
        campaign_type = "daily momentum posts"

    strategy = {
        "best_time_to_post": timing,
        "preferred_platform": best_platform,
        "campaign_type": campaign_type,
        "language": lang,
        "date_generated": str(datetime.datetime.utcnow()),
        "user_id": user_data.get("user_id", "anonymous")
    }

    log_user_insight(user_id=str(user_data.get("user_id", "unknown")),
                     insight_type="growth_strategy",
                     data=strategy)

    return strategy


