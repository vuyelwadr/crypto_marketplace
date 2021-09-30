from django.shortcuts import render, redirect
from .models import CustomUser, Btc_Details, Fiat_Details, Fiat_Transactions
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import auth
from bit import Key, PrivateKeyTestnet, wif_to_key
from datetime import date
from pycoingecko import CoinGeckoAPI


def index(request):
    if request.user.is_authenticated:
        userid = request.user.id
        details = refreshwallet(request)
        
        return render(request, 'dashboard.html', details)
        # return render(request, 'index.html', {'userdetails' : userdetails, 'btcdetails' : btcdetails, 'fiatdetails' : fiatdetails})
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

                # Link user details to Fiat_Details Table and Give the user 1000USD to start with
                fiatdetail = Fiat_Details(user.id, balance=1000) 
                fiatdetail.save()

                # Record 1000USD deposit into user's account
                fiattransactions = Fiat_Transactions(user.id, date=str(date.today()), amount=1000, transaction_type='Deposit', notes='Initial Deposit')
                fiattransactions.save()

                print('User Created')
                return redirect('login')

        else:
            messages.info(request, 'Password Not Matching')
            return redirect('register')
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
    transactions = bitcoin_key.get_transactions()

    # Temp values during dev will have to delete
    # balance_btc = 0
    # balance_usd = 0
    # transactions = 0

    btcdetail = Btc_Details(userid, public_key=public_key, private_key=private_key, balance_btc=balance_btc, balance_usd=balance_usd, transactions=transactions)
    btcdetail.save()

    btcdetails = Btc_Details.objects.prefetch_related().get(id=userid)
    fiatdetails = Fiat_Details.objects.prefetch_related().get(id=userid)
    transactiondetails = Fiat_Transactions.objects.prefetch_related().get(id=userid)


    # Shows that the values were refreshed, can delete this after dev
    # messages.info(request, "Text Area")
    details = {'userdetails' : userdetails, 'btcdetails' : btcdetails, 'fiatdetails' : fiatdetails, 'transactiondetails' : transactiondetails, 'btcprice' : btcprice}

    return details

def btc_buy(request):

    details = refreshwallet(request)
    fiatdetail = details.get("fiatdetails")
    userdetails = details.get("userdetails")
    if request.method == 'POST':
        usdamount = request.POST['usdamount']  
        # Admin account has id 1
        if (fiatdetail.balance > usdamount):
            admindetails = CustomUser.objects.prefetch_related().get(id=1)
            adminwallet = PrivateKeyTestnet(admindetails.private_key)

            try:
                tx_1 = adminwallet.send([(userdetails.public_key, usdamount, 'usd')], fee=1000, absolute_fee=True)
            except :
                messages.info(request,"Transaction Failed")
            else:
                fiat(request, "Buy", usdamount)
                details = refreshwallet(request)
                messages.success(request,"Transaction Successful, transaction id: " + tx_1 )

        else:
            messages.info(request, "Insufficient funds")

    return render(request, 'btc_buy.html', details)

def btc_sell(request):
    details = refreshwallet(request)
    fiatdetail = details.get("fiatdetails")
    btcdetails = details.get("btcdetails")
    userdetails = details.get("userdetails")
    if request.method == 'POST':
        usdamount = request.POST['usdamount']


        if (btcdetails.balance_usd >= usdamount):
            admindetails = CustomUser.objects.prefetch_related().get(id=1)
            userwallet = PrivateKeyTestnet(userdetails.private_key)

            try:
                tx_1 = userwallet.send([(admindetails.public_key, usdamount, 'usd')], fee=1000, absolute_fee=True)
            except :
                messages.info(request,"Transaction Failed")
            else:
                fiat(request, "Sell", usdamount)
                details = refreshwallet(request)
                messages.success(request,"Transaction Successful, transaction id: " + tx_1 )
        else:
            messages.info(request, "Insufficient funds")

    return render(request, 'btc_sell.html', details)

def fiat(request,transaction, sum):
    details = refreshwallet(request)
    userid = request.user.id;
    fiatdetails = details.get("fiatdetails")
    transactiondetails = details.get("transactiondetails")
    
    if (transaction == "Buy"):
        fiatdetail = Fiat_Details(userid, balance=(int(fiatdetails.balance)-int(sum))) 
        fiatdetail.save()

        fiattransactions = Fiat_Transactions.objects.create(userid=userid, date=str(date.today()), amount=sum, transaction_type='Buy', notes='BTC Buy')
    
    elif (transaction == "Sell"):
        fiatdetail = Fiat_Details(userid, balance=(int(fiatdetails.balance)+int(sum))) 
        fiatdetail.save()

        fiattransactions = Fiat_Transactions.objects.create(userid=userid, date=str(date.today()), amount=sum, transaction_type='Sell', notes='BTC Sell')