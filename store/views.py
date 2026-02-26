from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.signals import user_logged_in
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Category, Product, CartItem, Order, OrderItem
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ProductSerializer, CategorySerializer
from .utils import convert_price,CURRENCY_SYMBOLS
from django.contrib.auth.signals import user_logged_out
from .forms import AddressForm

import uuid
import json




@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.filter(is_available=True)
    paginator = Paginator(products, 9)

    page = request.query_params.get('page', 1)
    products_page = paginator.get_page(page)   

    serializer = ProductSerializer(products_page, many=True)

    return Response({
        'products': serializer.data,
        'count': products_page.paginator.count,
        'current_page': products_page.number,
        'total_pages': products_page.paginator.num_pages
    })


def cart_count(request):
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
    else:
        session_id = request.session.session_key
        count = CartItem.objects.filter(session_id=session_id).count()
    return JsonResponse({'count': count})



def product(request):
    category_slug = request.GET.get('category')
    products = Product.objects.filter(is_available=True)
    if category_slug:
        products = products.filter(category__slug=category_slug)

    selected_currency = request.session.get('currency', 'INR')
    for p in products:
        p.converted_price = convert_price(p.price, selected_currency)

    paginator = Paginator(products, 9)  # 9 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, 'store/products.html', {
        'page_obj': page_obj,
        'currency': selected_currency,
        'categories': categories,
        'category_slug': category_slug,
        'query': request.GET.get('q', '')
    })


@api_view(['GET'])
def category_list_api(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)

def home(request):
    featured_products = Product.objects.filter(is_available=True)[:8]
    categories = Category.objects.all()[:6]

    selected_currency = request.session.get('currency', 'INR')
    for p in featured_products:
        p.converted_price = convert_price(p.price, selected_currency)

    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'currency': selected_currency
    })

@login_required
def product_detail(request, id):
    product = get_object_or_404(Product, id=id, is_available=True)
    selected_currency = request.session.get('currency', 'INR')
    product.converted_price = convert_price(product.price, selected_currency)

    return render(request, 'store/product_detail.html', {
        'product': product,
        'currency': selected_currency
    })

@login_required
def product_detail1(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    selected_currency = request.session.get('currency', 'INR')
    product.converted_price = convert_price(product.price, selected_currency)

    return render(request, 'store/product_detail.html', {
        'product': product,
        'currency': selected_currency
    })

@login_required 
def account_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5] 
    return render(request, 'store/accounts.html', { 'orders': orders, })


@login_required
@require_http_methods(["POST"])
def add_to_cart(request):
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))

    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product_id=product_id,
            defaults={'quantity': quantity}
        )
    else:
        session_id = request.session.session_key or request.session.create()
        cart_item, created = CartItem.objects.get_or_create(
            session_id=session_id,
            product_id=product_id,
            defaults={'quantity': quantity}
        )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    # If AJAX request → return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        count = CartItem.objects.filter(
            user=request.user if request.user.is_authenticated else None,
            session_id=None if request.user.is_authenticated else request.session.session_key
        ).count()
        return JsonResponse({'status': 'success', 'count': count})

    # Otherwise → redirect to cart page
    return redirect('cart')

@login_required
def checkout(request):
    selected_currency = request.session.get('currency', 'INR')
    symbol = CURRENCY_SYMBOLS.get(selected_currency, selected_currency)

    cart_items = CartItem.objects.filter(user=request.user, status='active')

    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty')
        return redirect('cart')

    total = 0
    for item in cart_items:
        unit_price = convert_price(item.product.price, selected_currency)
        item.unit_price = unit_price
        total += unit_price * item.quantity

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()

            # Now create the order after address is saved
            order = Order.objects.create(
                user=request.user,
                order_number=f'ORD-{uuid.uuid4().hex[:8].upper()}',
                total_amount=total,
                currency=selected_currency,
                status='pending',
                shipping_address=address  # link address to order
            )

            for item in cart_items:
                unit_price = convert_price(item.product.price, selected_currency)
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=unit_price
                )
            return redirect('payment')  # or confirmation page
    else:
        form = AddressForm()

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'currency': selected_currency,
        'currency_symbol': symbol,
        'form': form
    })

@login_required
def track_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'store/orders.html', {'order': order})

@login_required
def payment(request):
    order = Order.objects.filter(user=request.user, status="pending").last()

    if request.method == "POST":
        # simulate payment success
        order.status = "paid"
        order.save()

        # now clear cart
        # CartItem.objects.filter(user=request.user, status="active").delete()

        messages.success(request, "Payment successful!")
        return redirect("track_order", order_number=order.order_number)

    return render(request, "store/payment.html", {"order": order})





@csrf_exempt
@login_required   
def verify_payment(request):
    if request.method == 'POST':
        cart_items = CartItem.objects.filter(user=request.user)
        selected_currency = request.session.get('currency', 'INR')

        total = 0
        for item in cart_items:
            unit_price = convert_price(item.product.price, selected_currency)
            total += unit_price * item.quantity

        order = Order.objects.create(
            user=request.user,
            order_number=f'ORD-{uuid.uuid4().hex[:8].upper()}',
            total_amount=total,
            currency=selected_currency,  # save currency type
            status='pending'
        )

        for item in cart_items:
            unit_price = convert_price(item.product.price, selected_currency)
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=unit_price
            )

        cart_items.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'})


# views.py


def cart_view(request):
    selected_currency = request.session.get('currency', 'INR')
    symbol = CURRENCY_SYMBOLS.get(selected_currency, selected_currency)

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user, status='active')
    else:
        cart_items = CartItem.objects.filter(session_id=request.session.session_key, status='active')

    total = 0
    items = []
    for item in cart_items:
        subtotal = item.product.price * item.quantity
        converted_subtotal = convert_price(subtotal, selected_currency)
        items.append({
            'product': item.product,
            'quantity': item.quantity,
            'subtotal': converted_subtotal
        })
        total += converted_subtotal

    context = {
        'cart_items': items,
        'total': total,
        'currency': selected_currency,
        'currency_symbol': symbol,
    }
    return render(request, 'store/cart.html', context)






def clear_cart_on_login(sender, user, request, **kwargs):
    # Reset cart count when user logs in
    CartItem.objects.filter(user=user).delete()
    request.session['cart'] = {}

    user_logged_in.connect(clear_cart_on_login)

def subscribe_newsletter(request):
    if request.method == "POST":
        email = request.POST.get("email")
        # Save email to DB or mailing list here
        messages.success(request, "Thank you for subscribing!")
        return redirect("home")  # or wherever you want to redirect
    return render(request, "newsletter.html")


def refund_policy(request):
    return render(request, "store/refund_policy.html")

def privacy_policy(request):
    return render(request, "store/privacy_policy.html")

def terms_service(request):
    return render(request, "store/terms_service.html")

def shipping_policy(request):
    return render(request, "store/shipping_policy.html")

def contact(request):
    return render(request, "store/contact.html")



@require_http_methods(["POST"])
def decrease_item(request, product_id):
    if request.user.is_authenticated:
        cart_item = CartItem.objects.filter(user=request.user, product_id=product_id, status='active').first()
    else:
        cart_item = CartItem.objects.filter(session_id=request.session.session_key, product_id=product_id, status='active').first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')


@require_http_methods(["POST"])
def remove_item(request, product_id):
    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user, product_id=product_id, status='active').delete()
    else:
        CartItem.objects.filter(session_id=request.session.session_key, product_id=product_id, status='active').delete()
    return redirect('cart')


def clear_cart_on_logout(sender, request, user, **kwargs):
    # Delete only active items, keep pending ones
    CartItem.objects.filter(user=user, status='active').delete()
    request.session['cart'] = {}
    user_logged_out.connect(clear_cart_on_logout)


@require_http_methods(["POST"])
def set_currency(request):
    currency = request.POST.get('currency', 'INR')
    request.session['currency'] = currency
    return JsonResponse({'status': 'success', 'currency': currency})
