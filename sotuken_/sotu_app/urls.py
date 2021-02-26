"""sotu_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path,include
from django.views.generic.base import TemplateView
from django.contrib.auth import views as auth_views
from sotuken import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sotuken/', include('sotuken.urls')),
    path('sotuken/', include('django.contrib.auth.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'), 
    path('password_reset/',views.forgotPassword, name='password_reset'),
    path('password_reset_submit/',views.forgotPasswordSubmit, name='password_reset_submit'),
    path('reset/<token>/',views.forgotPassword2, name='forgotPassword2'),
    path('login/', views.login_view, name='login'),
]