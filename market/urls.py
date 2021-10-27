from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index,  name='index'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('btc_buy', views.btc_buy, name='btc_buy'),
    path('btc_sell', views.btc_sell, name='btc_sell'),
    path('usd_deposit', views.usd_deposit, name='usd_deposit'),
    path('usd_withdraw', views.usd_withdraw, name='usd_withdraw'),
    path('help', views.help, name='help'),
    path('review', views.review, name='review'),
    path('user_requests', views.user_requests, name='user_requests'),
    path('user_details', views.user_details, name='user_details'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
