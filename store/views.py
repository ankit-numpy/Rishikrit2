from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .cart import add_to_cart, get_cart_items, remove_from_cart, set_quantity
from .forms import CheckoutForm
from .models import Coupon, DeliveryRate, Order, OrderItem, Product


def home(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'store/home.html', {'products': products})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'store/product_detail.html', {'product': product})


def cart_view(request):
    items, total = get_cart_items(request)
    return render(request, 'store/cart.html', {'items': items, 'total': total})


def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if product.inventory <= 0:
        messages.error(request, 'This item is currently out of stock.')
        return redirect('cart')

    quantity = int(request.POST.get('quantity', 1))
    add_to_cart(request, product.id, quantity)
    messages.success(request, f'Added {product.name} to cart.')
    return redirect('cart')


def update_cart(request, product_id):
    quantity = int(request.POST.get('quantity', 1))
    set_quantity(request, product_id, quantity)
    return redirect('cart')


def remove_cart(request, product_id):
    remove_from_cart(request, product_id)
    return redirect('cart')


def _get_active_delivery():
    return DeliveryRate.objects.filter(is_active=True).first()


def _calculate_discount(subtotal, coupon):
    if not coupon:
        return Decimal('0.00')
    if subtotal < coupon.min_order_amount:
        return Decimal('0.00')
    if coupon.discount_type == 'percent':
        return (subtotal * coupon.value / Decimal('100.0')).quantize(Decimal('0.01'))
    return min(coupon.value, subtotal)


@transaction.atomic

def checkout(request):
    items, subtotal = get_cart_items(request)
    if not items:
        messages.info(request, 'Your cart is empty.')
        return redirect('home')

    active_delivery = _get_active_delivery()

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            coupon_code = form.cleaned_data.get('coupon_code', '')
            coupon = None
            if coupon_code:
                coupon = Coupon.objects.filter(code=coupon_code, active=True).first()
                if not coupon or not coupon.is_valid():
                    messages.error(request, 'Invalid or expired coupon code.')
                    return redirect('checkout')

            discount = _calculate_discount(subtotal, coupon)
            delivery_fee = active_delivery.calculate_fee(subtotal - discount) if active_delivery else Decimal('0.00')

            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.coupon = coupon
            order.discount_amount = discount
            order.delivery_fee = delivery_fee

            if order.payment_method == 'cod':
                order.payment_status = 'pending'
            else:
                order.payment_status = 'pending'

            order.save()

            for item in items:
                product = item['product']
                quantity = item['quantity']
                if product.inventory < quantity:
                    messages.error(
                        request,
                        f'Insufficient stock for {product.name}. Please update your cart.'
                    )
                    return redirect('cart')

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                )
                product.inventory -= quantity
                product.save()

            if coupon:
                coupon.used_count += 1
                coupon.save(update_fields=['used_count'])

            request.session['cart'] = {}
            return redirect(reverse('order_success', args=[order.id]))
    else:
        form = CheckoutForm()

    discount = Decimal('0.00')
    delivery_fee = active_delivery.calculate_fee(subtotal) if active_delivery else Decimal('0.00')
    total = subtotal - discount + delivery_fee

    context = {
        'form': form,
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'delivery_fee': delivery_fee,
        'total': total,
        'delivery_rate': active_delivery,
    }
    return render(request, 'store/checkout.html', context)


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/order_success.html', {'order': order})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('order_history')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})


@login_required

def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})


@login_required

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})
