from django.urls import path
from . import views

urlpatterns = [
    path('', views.index,  name='index'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('btc_buy', views.btc_buy, name='btc_buy'),
    path('btc_sell', views.btc_sell, name= 'btc_sell'),
]