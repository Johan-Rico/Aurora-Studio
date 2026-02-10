from django.views import View
from django.shortcuts import render, redirect
from .models import Product
from .services import CreateOrderService
from .infra.factories import PaymentFactory

class CreateOrderView(View):

    def setup_service(self):
        gateway = PaymentFactory.get_payment_processor()
        return CreateOrderService(payment_processor=gateway)
    
    def get(self, request):
        context = {'products': Product.objects.all(), **CreateOrderService.get_cart_details(request.session.get('cart', {}))}
        return render(request, 'aurora_studio_app/home.html', context)

    def post(self, request):
        service = self.setup_service()
        action = request.POST.get('action')
        
        if action == 'create_order':
            cart = request.session.get('cart', {})
            if cart:
                service.create_order_from_cart(cart)
                request.session['cart'] = {}
                request.session.modified = True
            return redirect('home')
        
        request.session['cart'] = service.handle_cart_action(
            request.session.get('cart', {}), action, request.POST.get('product_id')
        )
        request.session.modified = True
        return redirect('home')