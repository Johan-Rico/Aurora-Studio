from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Order, OrderItem

class CreateOrderView(View):
    
    def get(self, request):
        products = Product.objects.all()
        cart = request.session.get('cart', {})
        
        cart_items = []
        total = 0
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            subtotal = product.price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
        
        context = {
            'products': products,
            'cart_items': cart_items,
            'total': total
        }
        return render(request, 'aurora_studio_app/home.html', context)

    def post(self, request):
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        cart = request.session['cart']
        
        if action == 'add':
            if product_id in cart:
                cart[product_id] += 1
            else:
                cart[product_id] = 1
        
        elif action == 'remove':
            if product_id in cart:
                cart[product_id] -= 1
                if cart[product_id] <= 0:
                    del cart[product_id]
        
        elif action == 'create_order':
            if cart:
                order = Order.objects.create()
                for prod_id, quantity in cart.items():
                    product = get_object_or_404(Product, id=prod_id)
                    for _ in range(quantity):
                        OrderItem.objects.create(order=order, product=product, price=product.price)
                request.session['cart'] = {}
        
        request.session.modified = True
        return redirect('home')