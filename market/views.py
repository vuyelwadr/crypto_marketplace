from django.shortcuts import render, redirect
from .models import CustomUser, Btc_Details, Fiat_Details, Fiat_Transactions, User_Requests, Reviews
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import auth
from bit import Key, PrivateKeyTestnet, wif_to_key
from datetime import date
from pycoingecko import CoinGeckoAPI
import random   
import string  
import secrets
from django.utils.safestring import mark_safe
import requests
from django.utils.datastructures import MultiValueDictKeyError
from django.db.models import Sum, Count


def index(request):
    if request.user.is_authenticated:
        userid = request.user.id
        details = refreshwallet(request)
        userdetails = details.get("userdetails")
        
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
                    # make sure eusernamemail isn't taken
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
        user = auth.authenticate(username=username, password=password)
        
        if user is not None:
            auth.login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'Invalid login')
            return redirect('login')
    else:
        return render(request, 'login.html')

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
                if (fiatdetail.balance > int(usdamount)):
                    admindetails = CustomUser.objects.prefetch_related().get(id=1)
                    adminwallet = PrivateKeyTestnet(admindetails.private_key)
                    if (transaction_priority=="1"):
                        tx_1 = adminwallet.send([(userdetails.public_key, usdamount, 'usd')])
                        messages.info(request, "Fast")
                    else:
                        tx_1 = adminwallet.send([(userdetails.public_key, usdamount, 'usd')], fee=5000, absolute_fee=True)
                        messages.info(request, "Normal")
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

            try:
                if (btcdetails.balance_usd >= usdamount):
                    admindetails = CustomUser.objects.prefetch_related().get(id=1)
                    userwallet = PrivateKeyTestnet(userdetails.private_key)

                    tx_1 = userwallet.send([(admindetails.public_key, usdamount, 'usd')], fee=5000, absolute_fee=True)
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
                    user_request(request, "Deposit", usdamount, reference, proof, "", "")
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

        if request.method == 'POST':
            usdamount = request.POST['usdamount']
            bank_name = request.POST['bank_name']
            account_number = request.POST['account_number']
            
            try:
                proof = request.FILES['proof']
                if (int(usdamount)<=int(fiatdetails.balance) and len(bank_name)>0 and len(account_number)>0) :
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
        if request.method == 'POST':
            url = "https://twinword-sentiment-analysis.p.rapidapi.com/analyze/"
            headers = {
                'content-type': "application/x-www-form-urlencoded",
                'x-rapidapi-host': "twinword-sentiment-analysis.p.rapidapi.com",
                'x-rapidapi-key': "42e11407a8msh3e7bfe671792741p13625fjsn79c7af84436e"
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
        return render(request,'review.html')
    else:
        return index(request)

def user_details(request):
    if request.user.is_authenticated:
        userid = request.user.id
        if request.method == 'POST':
            bank_name = request.POST['bank_name']
            account_name = request.POST['account_name']
            account_number = request.POST['account_number']
            try:
                if (bank_name != "None" and account_name != "" and account_number != ""):
                    fiatdetail = Fiat_Details.objects.get(id = userid) 
                    fiatdetail.bank_details = bank_name
                    fiatdetail.account_name = account_name
                    fiatdetail.account_number = account_number
                    fiatdetail.save()
                    messages.success(request, "Details Saved")
                else:
                    messages.info(request, "Enter valid details")
            except:
                messages.info(request, "Failed to save details")
            
        return render(request, 'user_details.html')
    else:
        return index(request)


def contact_us(request):
    # https://www.section.io/engineering-education/how-to-send-email-in-django/
    return render(request,'contact_us.html')

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



def user_request(request, t_type, amount, reference, proof, bank, account):
    userid = request.user.id;
 
        # if user enters a non integer value throw a transaction
    if (t_type == "Deposit" or t_type == "Withdraw"):
        userrequest = User_Requests.objects.create(user_id=userid, amount=amount, request=t_type, reference=reference, proof=proof, date=str(date.today()), status="Pending")