from django.urls import path
from . import views

urlpatterns = [
  path('url/', views.DAuthUrl.as_view(), name='index'),
  path('auth/', views.GetDodamUser.as_view(), name='index'),
  path('posting/', views.UserPosting.as_view(), name='index'),
]
