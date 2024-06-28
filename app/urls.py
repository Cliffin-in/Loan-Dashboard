from django.urls import path
from .views import *


urlpatterns = [
    path('create-access-token',CreateAccessToken.as_view()),
    path('opp-by-pipeline',opp_list_by_pipeline),
    path('opp-by-stage',opp_list_by_stage),
    path('list-pipelines',list_pipelines)
]
