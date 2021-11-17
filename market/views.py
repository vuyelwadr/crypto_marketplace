from django.shortcuts import render, redirect
from .models import CustomUser, Btc_Details, Fiat_Details, Fiat_Transactions, User_Requests, Reviews
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import auth, AbstractUser
from bit import Key, PrivateKeyTestnet, wif_to_key
from datetime import date, datetime, timedelta
from pycoingecko import CoinGeckoAPI
import random   
import string  
import secrets
from django.utils.safestring import mark_safe
import requests
from django.utils.datastructures import MultiValueDictKeyError
from django.db.models import Sum, Count
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
import matplotlib.pyplot as plt
import numpy as np
import sys

# Bitcoin transaction fees
# if update change in btc buy, sell and withdraw pages
btc_transaction_fee = 3
btc_fast_transaction_fee = 10


def index(request):
    # https://www.w3schools.com/python/matplotlib_pie_charts.asp
    if request.user.is_authenticated:
        userid = request.user.id
        details = refreshwallet(request)
        userdetails = details.get("userdetails")
        fiatdetails = details.get("fiatdetails")
        btcdetails = details.get("btcdetails")
        
        # Asset pie chart
        y = np.array([float(btcdetails.balance_usd), float(fiatdetails.balance)])
        # y = np.array([0, 100])
        color = ("#ffa500","#555")
        total = sum(y)
        mylabels = ["Bitcoin", "USD"]

        plt.pie(y, labels=mylabels,colors=color, autopct=lambda p: '{:.0f}%'.format(p * total / 100))
        # plt.show() 
        # plt.savefig('market/static/img/assets.png' ,bbox_inches='tight')
        plt.savefig('market/static/img/assets.png' ,bbox_inches='tight')
        # sys.stdout.flush()


        return render(request, 'dashboard.html', details)
    else:
        sentiments = Reviews.objects.all()
        sentiment = sentiments.aggregate(Sum('sentiment_score')).get("sentiment_score__sum")
        str_sentiment = "Site Sentiment score: " + str(sentiment)
        if (sentiment < 0):
            str_sentiment += " Negative"
        elif (sentiment == 0):
            str_sentiment += " Neutral"
        elif (sentiment > 0):
            str_sentiment += " Positive"

        transactions = Fiat_Transactions.objects.all()
        # btc_buy = sentiments.aggregate(Count('transaction_type'))
        btc_transactions = transactions.values('transaction_type').annotate(dcount=Count('transaction_type'))
        # transactions.values('Buy').annotate(dcount=Count('transaction_type'))
        btc_transactions_buy = btc_transactions.get(transaction_type="Buy").get("dcount")
        btc_transactions_sell = btc_transactions.get(transaction_type="Sell").get("dcount")
        total_transactions = btc_transactions_buy + btc_transactions_sell

        messages.info(request, str_sentiment)
        messages.info(request, "Total Transactions: "+ str(total_transactions))
        return render(request, 'index.html')

def register(request):
    # Generate bitcoin key
    bitcoin_key = PrivateKeyTestnet()
    public_key = bitcoin_key.address
    # use wallet import format to get bitcoin private key
    private_key = bitcoin_key.to_wif()

    balance_btc = bitcoin_key.get_balance('btc')
    balance_usd = bitcoin_key.get_balance('usd')
    # This query makes loading slow
    transactions = bitcoin_key.get_transactions() 


    if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']

        try:
            # make sure password matches
            if password==password2:       
                # make sure email isn't taken
                if CustomUser.objects.filter(email=email).exists():
                    messages.info(request, 'Email Taken')
                    return redirect('register')
                    # make sure username isn't taken
                elif CustomUser.objects.filter(username=username).exists():
                    messages.info(request, 'Username Taken')
                    return redirect('register')
                else:
                    user = CustomUser.objects.create_user(username=username, email=email, password=password, private_key=private_key, public_key=public_key)
                    user.save()

                    # Link user details to Btc_Details Table
                    btcdetail = Btc_Details(user.id, public_key=public_key, private_key=private_key, balance_btc=balance_btc, balance_usd=balance_usd, transactions=transactions  )
                    btcdetail.save()

                    # Link user details to Fiat_Details Table and Give the user 100USD to start with
                    fiatdetail = Fiat_Details(user.id, balance=100) 
                    fiatdetail.save()

                    # Record 100USD deposit into user's account
                    fiattransactions = Fiat_Transactions(user.id, date=str(date.today()), amount=100, transaction_type='Deposit', notes='Initial Deposit')
                    fiattransactions.save()

                    messages.info(request, 'User Created')
                    return redirect('login')

            else:
                messages.info(request, 'Password Not Matching')
                return redirect('register')
        except:
            return redirect('/')
        return redirect('/')

    else:
        return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        request.session['username'] = request.POST['username']
        request.session['password'] = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        
        if user is not None:
            # auth.login(request, user)
            # return redirect('index')
            num = 6
            code = ''.join(secrets.choice(string.ascii_letters + string.digits) for x in range(num))
            date = datetime.utcnow() + timedelta(hours=2)
            date = date.strftime("%d/%m/%Y %H:%M:%S")
            email = user.email
            subject = "Login Request"
            message = "User " + user.username + " login request at " +  date + "\n" + "Login Code: " + code
            
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
            messages.success(request, "Login code sent successfully")

            request.session['code'] = str(code)
            return redirect('code_login')
        else:
            messages.info(request, 'Invalid login')
            return redirect('login')
    else:
        return render(request, 'login.html')

def code_login(request):
    # https://pypi.org/project/pyotp/
    # try:
    code = request.session['code']
    username = request.session.get('username')
    password = request.session.get('password')

    user = auth.authenticate(username=username, password=password)
    if request.method == 'POST':
        user_code = request.POST['code']
        if code == user_code:
            auth.login(request, user)
            return redirect('index')
        else:
            messages.info(request, "Enter a valid Code")
    return render (request, 'code_login.html', {'user' : user})
    # except:
    #     return index(request)

def forgot_password(request):
    # If the user is logged in then redirect to the details to reset there
    if request.user.is_authenticated:
        return redirect('user_details')
    else:
        if request.method == 'POST':
            username = request.POST['username']
            email = request.POST['email']
            request.session['username'] = request.POST['username']
            request.session['email'] = request.POST['email']
            # user = auth.authenticate(username=username, email=email)
            try:
                if CustomUser.objects.get(username=username) == CustomUser.objects.get(email=email) :
                    userdetail = CustomUser.objects.get(username=username) 
                    request.session['username'] = username
                    # user = auth.authenticate(username=username, password=username)
                else:
                    messages.info(request, "User doesn't exist")
            except:
                messages.info(request, "User doesn't exist")

            # try:
            num = 6
            code = ''.join(secrets.choice(string.ascii_letters + string.digits) for x in range(num))
            request.session['code'] = str(code)
            date = datetime.utcnow() + timedelta(hours=2)
            date = date.strftime("%d/%m/%Y %H:%M:%S")
            email = userdetail.email
            subject = "Password Reset Request"
            message = "User " + userdetail.username + " Password reset request at " +  date + "\n" + "Login Code: " + code
            
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
            return redirect('reset_password')
            # except:
            #     messages.info(request, "Error sending Code")

        return render(request,'forgot_password.html')

def reset_password(request):
    if request.user.is_authenticated:
        return redirect('user_details')
    else:
        try:
            username = request.session['username']
            userdetail = CustomUser.objects.get(username=username) 
        except:
            return redirect('login')

        if request.method == 'POST':
            code = request.POST['code']
            password1 = request.POST['password1']
            password2 = request.POST['password2']
            generated_code = request.session['code']
            try:
                if code == request.session['code']:
                    if  password1==password2:
                        userdetail = CustomUser.objects.get(username=username) 
                        # set_password hashes the password
                        userdetail.set_password(password1)
                        userdetail.save()
                        messages.success(request, "Password Changed")
                        return redirect('login')
                    else:
                        messages.info(request, "Passwords not matching")
                else:
                    messages.info(request, "Incorrect Code")
            except:
                messages.info(request, "Failed to save details")
        return render(request, 'reset_password.html', {'userdetail' : userdetail})

def logout(request):
    auth.logout(request)
    return redirect('index')


def btc_buy(request):
    if request.user.is_authenticated:
        details = refreshwallet(request)
        fiatdetail = details.get("fiatdetails")
        userdetails = details.get("userdetails")
        if request.method == 'POST':
            usdamount = request.POST['usdamount']  
            transaction_priority = request.POST['transaction_priority']
            # Admin account has id 1
            try:
                if (fiatdetail.balance > int(usdamount) + btc_transaction_fee):
                    admindetails = CustomUser.objects.prefetch_related().get(id=1)
                    adminwallet = PrivateKeyTestnet(admindetails.private_key) 
                    # add a $3 or $10 transaction fee fast transaction will revert to normal if insufficient funds
                    if (transaction_priority=="1" and fiatdetail.balance > int(usdamount) + btc_fast_transaction_fee):
                        tx_1 = adminwallet.send([(userdetails.public_key, usdamount, 'usd')])
                        fiat(request, "1", btc_fast_transaction_fee, tx_1)
                        messages.info(request, "Fast Transaction")
                    else:
                        tx_1 = adminwallet.send([(userdetails.public_key, usdamount, 'usd')], fee=5000, absolute_fee=True)
                        fiat(request, "0", btc_transaction_fee, tx_1)
                        messages.info(request, "Normal Transaction")
                    fiat(request, "Buy", usdamount, tx_1)
                    details = refreshwallet(request)
                    messages.success(request, mark_safe("Transaction Successful, transaction id: " + tx_1 + "<br/>" + "To see your transaction use the following link: <br/> https://blockstream.info/testnet/tx/" + tx_1))
                else:
                    messages.info(request, "Insufficient funds")
            except:
                messages.info(request,"Transaction Failed") 

        return render(request, 'btc_buy.html', details)
    else:
        return login(request)

def btc_sell(request):
    if request.user.is_authenticated:
        details = refreshwallet(request)
        fiatdetail = details.get("fiatdetails")
        btcdetails = details.get("btcdetails")
        userdetails = details.get("userdetails")
        if request.method == 'POST':
            usdamount = request.POST['usdamount']
            transaction_priority = request.POST['transaction_priority']

            try:
                if (btcdetails.balance_usd >= usdamount+btc_transaction_fee):
                    admindetails = CustomUser.objects.prefetch_related().get(id=1)
                    userwallet = PrivateKeyTestnet(userdetails.private_key)
                    if (transaction_priority=="1"):
                        tx_1 = userwallet.send([(admindetails.public_key, usdamount, 'usd')])
                        messages.info(request, "Fast Transaction")
                    else:
                        tx_1 = userwallet.send([(admindetails.public_key, usdamount, 'usd')], fee=5000, absolute_fee=True)
                        messages.info(request, "Normal Transaction")
                    
                    fiat(request, "Sell", usdamount, tx_1)
                    details = refreshwallet(request)
                    messages.success(request, mark_safe("Transaction Successful, transaction id: " + tx_1 + "<br/>" + "To see your transaction use the following link: <br/> https://blockstream.info/testnet/tx/" + tx_1))
                else:
                    messages.info(request, "Insufficient funds")
            except :
                messages.info(request,"Transaction Failed") 

        return render(request, 'btc_sell.html', details)
    else:
        return index(request)


def usd_deposit(request):
    if request.user.is_authenticated:
        details = refreshwallet(request)
        # Number of digits in reference
        num = 12
        reference = ''.join(secrets.choice(string.ascii_letters + string.digits) for x in range(num))
        details['reference'] = reference

        if request.method == 'POST':
            usdamount = request.POST['usdamount']   
            try:
                if int(usdamount) > 0 :
                    proof = request.FILES['proof']
                    user_request(request, "Deposit", usdamount, reference, proof, settings.DEFAULT_BANK, settings.DEFAULT_BANK_ACCOUNT)
                    messages.success(request,"Transaction Successful")
                else:
                    messages.info(request,"Enter a valid amount")
            except MultiValueDictKeyError:
                messages.info(request,"Upload Proof")
            except:
                messages.info(request,"Transaction Failed")
        
        return render(request, 'usd_deposit.html',details)
    else:
        return index(request)

def usd_withdraw(request):
    if request.user.is_authenticated:
        details = refreshwallet(request)
        fiatdetails = details.get("fiatdetails")
        # Number of digits in reference
        num = 12
        reference = ''.join(secrets.choice(string.ascii_letters + string.digits) for x in range(num))
        details['reference'] = reference
        bank_name = fiatdetails.bank_details
        account_number = fiatdetails.account_number

        if bank_name=="None" or account_number=="None":
            messages.info(request, "Please enter financials before withdrawing")
            return user_details(request)
       

        if request.method == 'POST':
            usdamount = request.POST['usdamount']
            
            
            try:
                proof = request.FILES['proof']
                if (int(usdamount)<=int(fiatdetails.balance)) :
                    user_request(request, "Withdraw", usdamount, reference, proof, bank_name, account_number )
                    messages.success(request,"Transaction Successful")
                else:
                    messages.info(request,"Transaction Failed")
            except MultiValueDictKeyError:
                messages.info(request,"Upload Proof")
            except:
                messages.info(request,"Transaction Failed")

        return render(request, 'usd_withdraw.html',details)
    else:
        return index(request)
    

def user_requests(request):
    if request.user.is_authenticated:
        refreshwallet(request)
        # details = refreshwallet(request)
        userid = request.user.id
        # Use objects.filter because it allows for iteration through the object
        # Only need fiat and requests for now
        userdetails = CustomUser.objects.filter(id=userid)
        btcdetails = Btc_Details.objects.filter(id=userid)
        fiatdetails = Fiat_Details.objects.filter(id=userid)
        transactiondetails = Fiat_Transactions.objects.filter(user_id=userid)
        userrequests = User_Requests.objects.filter(user_id=userid)
        details = {'userdetails' : userdetails, 'btcdetails' : btcdetails, 'fiatdetails' : fiatdetails, 'transactiondetails' : transactiondetails, 'userrequests' : userrequests}
        return render(request, 'user_requests.html' ,details)
    return index(request)


def review(request):
    if request.user.is_authenticated:
        userid = request.user.id
        details = refreshwallet(request)
        userdetails = details.get("userdetails")
        details["reviews"] = Reviews.objects.filter()
        if request.method == 'POST':
            url = "https://twinword-sentiment-analysis.p.rapidapi.com/analyze/"
            headers = {
                'content-type': "application/x-www-form-urlencoded",
                'x-rapidapi-host': "twinword-sentiment-analysis.p.rapidapi.com",
                'x-rapidapi-key': settings.RAPID_API_KEY
                }

            title = request.POST['title']
            body = request.POST['review']
            
            author = userid
            author_email = userdetails.email

            payload = {'text' : body}
            response = requests.request("POST", url, data=payload, headers=headers)
            temp_score = response.json()
            score = temp_score.get('score')

            if score>0:
                sentiment = "Positive"
            elif score== 0:
                sentiment = "Neutral"
            else:
                sentiment = "Negative"
            reviews = Reviews.objects.create(user_id=userid, author_email=userdetails.email, review_title=title, review_body=body, creation_date=str(date.today()), sentiment_score=score, sentiment=sentiment)
            messages.success(request, "Review Submitted")
        return render(request,'review.html', details)
    else:
        reviews = Reviews.objects.filter()
        return render(request,'review.html',{"reviews" :reviews})

def user_details(request):
    if request.user.is_authenticated:
        userid = request.user.id
        refreshwallet(request)
        # details = refreshwallet(request)
        userid = request.user.id
        # Use objects.filter because it allows for iteration through the object
        # Only need fiat and requests for now
        userdetails = CustomUser.objects.filter(id=userid)
        btcdetails = Btc_Details.objects.filter(id=userid)
        fiatdetails = Fiat_Details.objects.filter(id=userid)
        transactiondetails = Fiat_Transactions.objects.filter(user_id=userid)
        userrequests = User_Requests.objects.filter(user_id=userid)
        details = {'userdetails' : userdetails, 'btcdetails' : btcdetails, 'fiatdetails' : fiatdetails, 'transactiondetails' : transactiondetails, 'userrequests' : userrequests}
        if request.method == 'POST':
            if 'financials' in request.POST:
                bank_name = request.POST['bank_name']
                account_name = request.POST['account_name']
                account_number = request.POST['account_number']
                try:
                    fiatdetail = Fiat_Details.objects.get(id = userid) 
                    fiatdetail.bank_details = bank_name
                    fiatdetail.account_name = account_name
                    fiatdetail.account_number = account_number
                    fiatdetail.save()
                    messages.success(request, "Details Saved")
                except:
                    messages.info(request, "Failed to save details")
                
            if 'personal' in request.POST:
                first_name = request.POST['first_name']
                last_name = request.POST['last_name']
                try:
                    userdetail = CustomUser.objects.get(id = userid) 
                    userdetail.first_name = first_name
                    userdetail.last_name = last_name
                    userdetail.save()
                    messages.success(request, "Details Saved")
                except:
                    messages.info(request, "Failed to save details")

            if 'password' in request.POST:
                password1 = request.POST['password1']
                password2 = request.POST['password2']
                try:
                    if password1==password2:
                        userdetail = CustomUser.objects.get(id = userid) 
                        # set_password hashes the password
                        userdetail.set_password(password1)
                        userdetail.save()
                        messages.success(request, "Password Changed")
                        return redirect('login')
                    else:
                        messages.info(request, "Passwords not matching")
                except:
                    messages.info(request, "Failed to save details")

                
        return render(request, 'user_details.html', details)
    else:
        return index(request)


def contact_us(request):
    # https://www.section.io/engineering-education/how-to-send-email-in-django/
    if request.method == 'POST':
        try:
            name = request.POST['name']
            email = request.POST['email']
            phone = request.POST['phone']
            subject = request.POST['subject']
            message = request.POST['message']
            
            send_mail(subject, "Name: " + name + "\n" + "Email: " + email + "\n" + "Phone: " + phone + "\n" +"\n" + message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_TO_EMAIL])
            messages.success(request, "Email sent successfully")
        except:
            messages.info(request, "Failed to send email")

    return render(request,'contact_us.html')

def btc_deposit(request):
    if request.user.is_authenticated:
        userid = request.user.id
        details = refreshwallet(request)

        return render(request, 'btc_deposit.html', details)
    else:
        return index(request)

def btc_withdraw(request):
    if request.user.is_authenticated:
        userid = request.user.id
        details = refreshwallet(request)
        userdetails = details.get("userdetails")
        btcdetails = details.get("btcdetails")
        admindetails = CustomUser.objects.prefetch_related().get(id=1)
        if request.method == 'POST':
            usdamount = request.POST['usdamount']  
            btc_address = request.POST['btc_address']  
            transaction_priority = request.POST['transaction_priority']
            # try:
            if (int(float(btcdetails.balance_usd)) >= int(usdamount)+btc_transaction_fee):
                userwallet = PrivateKeyTestnet(userdetails.private_key)
                # convet float number to int
                if (transaction_priority=="1" and int(float(btcdetails.balance_usd)) > int(usdamount) + btc_fast_transaction_fee):
                        tx_1 = userwallet.send([(admindetails.public_key, usdamount, 'usd')])
                        messages.info(request, "Fast Transaction")
                else:
                    tx_1 = userwallet.send([(admindetails.public_key, usdamount, 'usd')], fee=5000, absolute_fee=True)
                    messages.info(request, "Normal Transaction")
                details = refreshwallet(request)
                messages.success(request, mark_safe("Transaction Successful, transaction id: " + tx_1 + "<br/>" + "To see your transaction use the following link: <br/> https://blockstream.info/testnet/tx/" + tx_1))
            else:
                messages.info(request, "Insufficient funds")
            # except:
            #     messages.info(request, "Transaction Failed")
        return render(request, 'btc_withdraw.html', details)
    else:
        return index(request)

def refreshwallet(request):
    
    # load all tables and create objects accessible in the html  file
    userid = request.user.id
    userdetails = CustomUser.objects.prefetch_related().get(id=userid)
    
    cg = CoinGeckoAPI()
    cg = cg.get_price(ids='bitcoin', vs_currencies='usd')
    btcprice = cg.get("bitcoin").get("usd")

    bitcoin_key = PrivateKeyTestnet(userdetails.private_key)
    private_key = bitcoin_key.to_wif()
    public_key = bitcoin_key.address

    # adds extra load time
    balance_btc = bitcoin_key.get_balance('btc')
    balance_usd = bitcoin_key.get_balance('usd')
    # transactions = bitcoin_key.get_transactions()

    # Temp values during dev will have to delete
    # balance_btc = 0
    # balance_usd = 0
    transactions = 0

    btcdetail = Btc_Details(userid, public_key=public_key, private_key=private_key, balance_btc=balance_btc, balance_usd=balance_usd, transactions=transactions)
    btcdetail.save()

    btcdetails = Btc_Details.objects.prefetch_related().get(id=userid)
    fiatdetails = Fiat_Details.objects.prefetch_related().get(id=userid)
    transactiondetails = Fiat_Transactions.objects.prefetch_related().get(id=userid)
    userrequests = User_Requests.objects.filter(user_id=userid)

    # Shows that the values were refreshed, can delete this after dev
    # messages.info(request, "Text Area")
    details = {'userdetails' : userdetails, 'btcdetails' : btcdetails, 'fiatdetails' : fiatdetails, 'transactiondetails' : transactiondetails, 'btcprice' : btcprice, 'userrequests' : userrequests}

    return details


def fiat(request,transaction, sum, reference):
    details = refreshwallet(request)
    userid = request.user.id;
    fiatdetails = details.get("fiatdetails")
    transactiondetails = details.get("transactiondetails")
    
    if (transaction == "Buy"):
        fiatdetail = Fiat_Details(userid, balance=(int(fiatdetails.balance)-int(sum))) 
        fiatdetail.save()

        fiattransactions = Fiat_Transactions.objects.create(user_id=userid, date=str(date.today()), amount=sum, transaction_type='Buy', notes='BTC Buy ID: '+reference)
    
    elif (transaction == "Sell"):
        fiatdetail = Fiat_Details(userid, balance=(int(fiatdetails.balance)+int(sum))) 
        fiatdetail.save()

        fiattransactions = Fiat_Transactions.objects.create(user_id=userid, date=str(date.today()), amount=sum, transaction_type='Sell', notes='BTC Sell ID: '+reference)

    elif (transaction == "1"):
        fiatdetail = Fiat_Details(userid, balance=(int(fiatdetails.balance)-int(sum))) 
        fiatdetail.save()

        fiattransactions = Fiat_Transactions.objects.create(user_id=userid, date=str(date.today()), amount=sum, transaction_type='Fee', notes='BTC Fast Transaction Fee: '+reference)

    elif (transaction == "0"):
        fiatdetail = Fiat_Details(userid, balance=(int(fiatdetails.balance)-int(sum))) 
        fiatdetail.save()

        fiattransactions = Fiat_Transactions.objects.create(user_id=userid, date=str(date.today()), amount=sum, transaction_type='Fee', notes='BTC Transaction Fee: '+reference)



def user_request(request, t_type, amount, reference, proof, bank, account):
    userid = request.user.id;
 
        # if user enters a non integer value throw a transaction
    if (t_type == "Deposit" or t_type == "Withdraw"):
        userrequest = User_Requests.objects.create(user_id=userid, amount=amount, request=t_type, reference=reference, bank_name = bank, account_number=account, proof=proof, date=str(date.today()), status="Pending")
