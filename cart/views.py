from django.shortcuts import render, redirect
from product.models import Product
from .models import Order, Cart, CartItem

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
import razorpay

razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))

@login_required
def initiate_payment(request):
    if request.method == 'POST':
        pid = request.POST.get('product_id')
        product = Product.objects.get(id=pid)
        currency = 'INR'
        amount = int(product.price * 100) # amount in paisa
        # create a razorpay order
        razorpay_order = razorpay_client.order.create({
            'amount': amount,
            'currency': currency,
            'payment_capture': '0' # auto capture
        })
        razorpay_order_id = razorpay_order['id']
        callback_url = request.build_absolute_uri('/payment/callback')
        request.session['product_id'] = pid
        ctx = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_merchant_key': settings.RAZOR_KEY_ID,
            'razorpay_amount': amount,
            'currency': currency,
            'callback_url': callback_url,
            'product': product
        }
        return render(request, 'cart/checkout.html', ctx)
    messages.error(request, 'Invalid request')  
    return redirect('home')  

# this function will be called after the payment is done
@csrf_exempt
def callback(request):
    if request.method == 'POST':
        # get the required parameters from post request.
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        result = razorpay_client.utility.verify_payment_signature(params_dict)
        if result:
            try:
                product = Product.objects.get(id=request.session['product_id'])
                order = Order(
                    user=request.user,
                    product=product,
                    address='12/123, abc street, xyz city',
                    is_paid = True,
                )
                order.save()
                razorpay_client.payment.capture(payment_id, int(order.product.price*100))
                return render(request, 'cart/success.html')
            except Exception as e:
                messages.error(request, 'Payment failed')
                return render(request, 'cart/failure.html')
        else:
            messages.error(request, 'Invalid payment details')
            return render(request, 'cart/failure.html')
    # if this url is accessed directly
    messages.error(request, 'Invalid request')
    return redirect('home')

def success_view(request):
    order = Order.objects.get(id=request.session['payment_info']['ORDERID'])
    return render(request, 'cart/success.html', {'order': order})

def failure_view(request):
    order = Order.objects.get(id=request.session['payment_info']['ORDERID'])
    return render(request, 'cart/failure.html', {'order': order})