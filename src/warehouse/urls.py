from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    path('', views.home, name="home"),
]
