from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/<uuid:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
]
