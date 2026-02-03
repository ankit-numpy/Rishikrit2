from .cart import get_cart_summary

def cart_summary(request):
    return get_cart_summary(request)
