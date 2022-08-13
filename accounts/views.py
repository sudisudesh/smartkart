from base64 import urlsafe_b64encode
from contextlib import redirect_stderr
from email import message
from email.policy import default
from pyexpat.errors import messages
import re
from textwrap import indent
from tkinter import N
from unittest.mock import DEFAULT
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib import messages ,auth
from django.contrib.auth.decorators import login_required

from accounts.forms import RegistrationForm
from accounts.models import Account


#verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from carts.models import CartItem


from carts.views import _cart_id
from carts.models import Cart, CartItem
import requests


# Create your views here.

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]
            
            user = Account.objects.create_user(first_name = first_name, last_name= last_name,  email = email, username= username , password= password )
            user.phone_number = phone_number
            user.save()
            
            #User activation
            current_site = get_current_site(request)
            mail_subject = 'Please Activate your account..!'
            message = render_to_string('accounts/account_verification_email.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            
            to_email = email
            send_email = EmailMessage(mail_subject, message, to =[to_email])
            send_email.send()
            
            # messages.success(request,'Thank you for Registrating ... We have sent a verification enamil to your email address .. please Active your account ')
            return redirect('/accounts/login/?command=verification&email='+email)
            
    else:
        form = RegistrationForm()
             
    context = {
        'form' : form,
    }
    return render(request, 'accounts/register.html',context)



def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(email=email , password=password)
        
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id = _cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart = cart).exists() 
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    
                    #getting the product veriation by cart id 
                    product_variation =[]
                    for item in cart_item:
                        variation = item.veriations.all()
                        product_variation.append(list(variation))
                    
                    #get the cart item from the userto access his product veriation
                    cart_item = CartItem.objects.filter(user=user)
                    ex_variation = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_variation.append(list(existing_variation))
                        id.append(item.id)
                        
                    for pr in product_variation:
                        if pr in ex_variation:
                            index = ex_variation.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id = item_id)
                            item.quantity+=1
                            item.user = user
                            item.save()
                        
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass
            auth.login(request, user )
            messages.success(request, ' You are now loged in ..')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
        
            except:
                return redirect('dashboard')
        
        else:
            messages.error(request, "invalid login id ")
            return redirect('login')
    return render(request, 'accounts/login.html')

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, ' You are logged out ')
    return redirect('login')



def activate(request , uidb64 , token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user= None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations ... Your account is activated..!')
        return redirect('login')
    else:
        messages.error(request, "Invalid activation link")
        return redirect("register")
    
    
@login_required(login_url = 'login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')



def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact= email)
            
        # reset password email acthentication
            current_site = get_current_site(request)
            mail_subject = 'Reset your password ..!'
            message = render_to_string('accounts/reset_password_email.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            
            to_email = email
            send_email = EmailMessage(mail_subject, message, to =[to_email])
            send_email.send()
            
            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        
        else:
            messages.error(request, 'Account does not exists..')
            return redirect('forgotPassword')
            
    return render(request ,'accounts/forgotPassword.html')

def resetpassword_validate(request , uidb64 , token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user= None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your Password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This link is expired..')
        return redirect('login')
    
    
def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset Successful..')
            return redirect('login')
            
        else:
            messages.error(request, 'Password Do not match .. try again')
            return redirect ('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')    
    
    
    

    
    