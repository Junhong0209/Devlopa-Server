from django.urls import path
from . import views

urlpatterns = [
  path('url/', views.DAuthUrl.as_view(), name='index'),
]
