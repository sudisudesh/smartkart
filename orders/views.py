from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect,render
from carts.models import CartItem
from .forms import OrderForm 
from django.db import models
from .models import Order


# Create your views here.
def place_order(request,total=0, quantity= 0):
    current_user = request.user
    
    cart_items = CartItem.objects.filter(user= current_user)
    cart_count = cart_items.count()
    if cart_count<= 0:
        return redirect('store')
    
    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = ( 2 * total)/100
    grand_total = total + tax
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            #store the all billing data into order table
            data = Order()
            data.user = current_user
            #['first_name','last_name','email','phone','address_line_1','address_line_2','city','state','pincode','order_note']
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.email = form.cleaned_data['email']
            data.phone = form.cleaned_data['phone']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.city = form.cleaned_data['city']
            data.state = form.cleaned_data['state']
            data.pincode = form.cleaned_data['pincode']
            data.order_note = form.cleaned_data['order_note']
            data.order_total =grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR') #this will give the user ip
            data.save()
            
            #Generate Order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()
            # return redirect('checkout')
            return render(request, 'checkout.html')
        
    else:
        return redirect('store')
    