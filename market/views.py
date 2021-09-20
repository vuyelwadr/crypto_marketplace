from django.shortcuts import render, redirect
from .models import CustomUser, Btc_Details, Fiat_Details, Fiat_Transactions
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import auth
from bit import Key, PrivateKeyTestnet, wif_to_key
from datetime import date

def index(request):
    # if request.user.is_authenticated:
    #     btcdetails = Btc_Details()
    #     details.public_key = CustomUser.public_key
    #     # btcwallet = PrivateKeyTestnet(str(CustomUser.private_key))
    #     btcaddress_private = CustomUser.private_key
    #     balance_btc = btcwallet.get_balance('btc')
    #     balance_usd = btcwallet.get_balance('usd')
    #     return render(request, 'index.html', {'details' : details})
    return render(request, 'index.html')

def register(request):
    # Generate bitcoin key
    bitcoin_key = PrivateKeyTestnet()
    private_key = bitcoin_key.address
    # use wallet import format to get bitcoin private key
    public_key = bitcoin_key.to_wif()

    balance_btc = bitcoin_key.get_balance('btc')
    balance_usd = bitcoin_key.get_balance('usd')
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