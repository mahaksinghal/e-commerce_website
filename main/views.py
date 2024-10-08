from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from product.models import Product, Category, Review
from product.forms import ReviewForm
from .models import SliderImage

# Create your views here.
def home_view(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    slider_images = SliderImage.objects.order_by('created_at')[:4]
    ctx = {
        'products': products,
        'categories': categories,
        'slider_images': slider_images,
    }
    return render(request, "home.html", ctx)

def logout_view(request):
    logout(request)
    return redirect("home")

# details of a product

def detail_view(request, id):
    product = Product.objects.get(id=id)
    # get upto 3 similar products
    # category = product.category
    similar_products = Product.objects.filter(category=product.category).exclude(id=id).order_by('?')[:3] # order by random
    # get latest reviews
    reviews = Review.objects.filter(product=product).order_by('-created_at') # reverse order
    # if user has review product, then allow to edit
    review = None
    if request.user.is_authenticated:
        review = Review.objects.filter(product=product, customer=request.user).first()
    if review:
        review_form = ReviewForm(instance=review)
    else:
        review_form = ReviewForm()
    ctx = {
        'product': product,
        'similar_products': similar_products,
        'reviews': reviews,
        # 'review_form': ReviewForm(),
        'review_form': review_form,
        'has_reviewed': True if review else False,
    }
    return render(request, 'details.html', ctx)

# category
def category_view(request, name):
    cat = get_object_or_404(Category, slug=name)
    products = get_list_or_404(Product, category=cat)
    return render(
        request, 'category_listing.html',
        context= {'products': products, 
                'cat': cat, 
                'categories': Category.objects.all()}
    )


# seller views
def seller_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username, password)
        error = False
        if not username:
            messages.error(request, "Username is required")
            error = True
        if not password:
            messages.error(request, "Password is required")
            error = True
        if not error:
            # check if user exists
            user = authenticate(username=username, password=password)
            if not user:
                messages.error(request, "Invalid username or password")
            else:
                # check if user is seller
                if user.groups.filter(name='seller').exists():
                    login(request, user)
                    messages.success(request, 'You are now logged in as seller')
                    return redirect('home')
                else:
                    messages.error(request, "You are not registered as a seller")
    return render(request, 'accounts/seller/login.html')

def seller_register_view(request):
    return render(request, 'accounts/seller/register.html')

def seller_forgot_pass_view(request):
    return render(request, 'accounts/seller/forgot_password.html')
# -------------------------------------------------------------------------------------------------
# customer views
def customer_login_view(request):
    return render(request, 'accounts/customer/login.html')

def customer_register_view(request):
    return render(request, 'accounts/customer/register.html')

def customer_forgot_pass_view(request):
    return render(request, 'accounts/customer/forgot_password.html')

# search
def search_view(request):
    query = request.GET.get('q')
    products = Product.objects.filter(title__icontains=query)
    category = Category.objects.filter(title__icontains=query)
    return render(
        request, 'search.html',
        context={
            'products': products,
            'categories': category,
            'query': query,
        }
    )

# review
def add_review(request, id):
    product = Product.objects.get(id=id)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.customer = request.user
        review.save()
        messages.success(request, 'Review added successfully')
    else:
        messages.error(request, 'Invalid form submission')
    return redirect('detail', id=id)

def edit_review(request, id):
    review = Review.objects.get(id=id)
    form = ReviewForm(request.POST, instance=review)
    if form.is_valid():
        form.save()
        messages.success(request, 'Review updated successfully')
    else:
        messages.error(request, 'Invalid form submission')
    return redirect('detail', id=review.product.id)