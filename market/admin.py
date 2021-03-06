from django.contrib import admin

# from .models import User_Requests, Reviews
from django.http import HttpResponse
from django.contrib import messages
from .models import CustomUser, Btc_Details, Fiat_Details, Fiat_Transactions, User_Requests, Reviews
from datetime import date
from django.contrib.admin import AdminSite
from django.utils.translation import ugettext_lazy


# Register your models here.

class Requests(admin.ModelAdmin):
    change_form_template = "admin_user_requests.html"

    list_display = ("user_id", "reference", "amount", "request", "status")
    list_filter = ("status",)
    search_fields = ["reference", "amount", "bank_name"]

    class Meta:
        model = User_Requests
        db_table = "tbl_temp_users"

    def response_change(self, request, obj):
        object_id = request.resolver_match.kwargs['object_id']
        
        if "Approve" in request.POST:
            fiat(request, object_id)
            return super(Requests, self).response_change(request, obj)
        elif "Deny" in request.POST:
            requests = User_Requests.objects.prefetch_related().get(id=object_id)
            requests.status='Rejected'
            requests.save()
            return super(Requests, self).response_change(request, obj)
        else:
            return super(Requests, self).response_change(request, obj)


def fiat(request, id):
    objectid = id;

    requests = User_Requests.objects.prefetch_related().get(id=objectid)
    sum = requests.amount
    userid = requests.user_id 
    request_type = requests.request

    fiatdetails = Fiat_Details.objects.prefetch_related().get(id=userid)
  
    if (request_type == "Deposit"):
            fiatdetail = Fiat_Details(id=userid, balance=(int(fiatdetails.balance)+int(sum)))
            fiatdetail.save()

            fiattransactions = Fiat_Transactions.objects.create(user_id=userid, date=str(date.today()), amount=sum, transaction_type='Deposit', notes='User Deposit')
            requests.status='Completed'
            requests.save()

    elif (request_type == "Withdraw"):
        if (sum > fiatdetails.balance):
            messages.error(request,"User has insufficient funds")
        else:
            fiatdetail = Fiat_Details(id=userid, balance=(int(fiatdetails.balance)-int(sum)))
            fiatdetail.save()

            fiattransactions = Fiat_Transactions.objects.create(user_id=userid, date=str(date.today()), amount=sum, transaction_type='Withdraw', notes='User Withdraw')
            requests.status='Completed'
            requests.save()
            


class Review(admin.ModelAdmin):
    list_display = ("id", "user_id", "review_title", "sentiment_score", "sentiment", "creation_date")
    list_filter = ("user_id", "sentiment")
    search_fields = ["sentiment", "review_title", "creation_date"]

    class Meta:
        model = Reviews
        db_table = "tbl_temp_users"


# admin.site.register = MyAdminSite()
admin.site.register(User_Requests, Requests)
admin.site.register(Reviews, Review)
# Change the default site header
admin.site.site_header = 'CryptoZ admin'