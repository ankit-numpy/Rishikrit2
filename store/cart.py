from decimal import Decimal
from .models import Product

CART_SESSION_KEY = 'cart'

def get_cart(request):
    return request.session.get(CART_SESSION_KEY, {})

def save_cart(request, cart):
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True

def add_to_cart(request, product_id, quantity=1):
    cart = get_cart(request)
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + quantity
    if cart[pid] <= 0:
        cart.pop(pid, None)
    save_cart(request, cart)


def set_quantity(request, product_id, quantity):
    cart = get_cart(request)
    pid = str(product_id)
    if quantity <= 0:
        cart.pop(pid, None)
    else:
        cart[pid] = quantity
    save_cart(request, cart)


def remove_from_cart(request, product_id):
    cart = get_cart(request)
    pid = str(product_id)
    cart.pop(pid, None)
    save_cart(request, cart)


def get_cart_items(request):
    cart = get_cart(request)
    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.filter(id__in=product_ids, is_active=True)
    items = []
    total = Decimal('0.00')

    for product in products:
        quantity = cart.get(str(product.id), 0)
        subtotal = product.price * quantity
        total += subtotal
        items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return items, total


def get_cart_summary(request):
    items, total = get_cart_items(request)
    count = sum(item['quantity'] for item in items)
    return {
        'cart_count': count,
        'cart_total': total,
    }
