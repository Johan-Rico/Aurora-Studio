from typing import Dict, List
from django.db import transaction
from .models import Product, Order, OrderItem


class CreateOrderService:

    def get_cart_details(cart: Dict[str, int]) -> Dict:
        cart_items = []
        total = 0
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                subtotal = product.price * quantity
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
            except Product.DoesNotExist:
                continue
        return {'cart_items': cart_items, 'total': total}
    

    def add_to_cart(cart: Dict[str, int], product_id: str) -> Dict[str, int]:
        cart[product_id] = cart.get(product_id, 0) + 1
        return cart
    

    def remove_from_cart(cart: Dict[str, int], product_id: str) -> Dict[str, int]:
        if product_id in cart:
            cart[product_id] -= 1
            if cart[product_id] <= 0:
                del cart[product_id]
        return cart
    
    def create_order_from_cart(cart: Dict[str, int]) -> Order:

        if not cart:
            raise ValueError("El carrito está vacío")
        
        order = Order.objects.create()
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )
        return order
    
    @staticmethod
    def handle_cart_action(cart: Dict[str, int], action: str, product_id: str = None) -> Dict[str, int]:
        """Maneja todas las acciones del carrito y retorna el carrito actualizado"""
        if action == 'add':
            return CreateOrderService.add_to_cart(cart, product_id)
        elif action == 'remove':
            return CreateOrderService.remove_from_cart(cart, product_id)
        elif action == 'create_order':
            if cart:
                CreateOrderService.create_order_from_cart(cart)
            return {}
        return cart
