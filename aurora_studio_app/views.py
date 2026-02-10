from django.views import View
from django.shortcuts import render, redirect
from .models import Product
from .services import CreateOrderService


class CreateOrderView(View):
    
    def get(self, request):
        context = {'products': Product.objects.all(), **CreateOrderService.get_cart_details(request.session.get('cart', {}))}
        return render(request, 'aurora_studio_app/home.html', context)

    def post(self, request):
        request.session['cart'] = CreateOrderService.handle_cart_action(
            request.session.get('cart', {}), request.POST.get('action'), request.POST.get('product_id')
        )
        request.session.modified = True
        return redirect('home')