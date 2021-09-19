from django.shortcuts import render, redirect
from .models import CustomUser
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import auth
from bit import Key, PrivateKeyTestnet, wif_to_key

def index(request):
    return render(request, 'index.html')

def register(request):
    # Generate bitcoin key
    bitcoin_key = PrivateKeyTestnet()
    private_key = bitcoin_key.address
    # use wallet import format to get bitcoin private key
    public_key = bitcoin_key.to_wif()

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
                user.save();
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