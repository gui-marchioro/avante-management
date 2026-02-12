from django.urls import NoReverseMatch, reverse
from .feature_routes import FEATURE_ROUTE_NAMES
from .models import CompanyFeature, get_user_company


def enabled_sidebar_features(request):
    if not getattr(request.user, "is_authenticated", False):
        return {"sidebar_features": []}

    company = get_user_company(request.user)
    if company is None:
        return {"sidebar_features": []}

    features = []
    grants = (
        CompanyFeature.objects.filter(
            company=company,
            enabled=True,
            feature__is_active=True,
        )
        .select_related("feature")
        .order_by("feature__code")
    )

    for grant in grants:
        route_name = FEATURE_ROUTE_NAMES.get(grant.feature.code)
        if route_name is None:
            continue
        try:
            features.append(
                {
                    "name": grant.feature.name,
                    "url": reverse(route_name),
                }
            )
        except NoReverseMatch:
            continue

    return {"sidebar_features": features}
