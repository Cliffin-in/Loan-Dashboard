from django.urls import path
from .views import *


urlpatterns = [
    path('create-access-token',CreateAccessToken.as_view()),
    path('opp-by-name',opp_by_name),
    path('opportunities-webhook',OpportunitiesWebhook.as_view())
]
