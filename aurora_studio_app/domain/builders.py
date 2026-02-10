from typing import Dict
from ..models import Order, OrderItem, Product

class OrderItemBuilder:
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.order = None
        self.product = None
        self.quantity = 1
        self.price = None
        return self
    
    def set_order(self, order):
        self.order = order
        return self
    
    def set_product(self, product):
        self.product = product
        self.price = product.price
        return self
    
    def set_quantity(self, quantity):
        if quantity <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        self.quantity = quantity
        return self
    
    def build(self) -> OrderItem:
        if self.order is None:
            raise ValueError("Debe especificar una orden")
        if self.product is None:
            raise ValueError("Debe especificar un producto")
        if self.price is None:
            raise ValueError("Debe especificar un precio")
        
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=self.quantity,
            price=self.price
        )
        
        self.reset()
        return order_item


class OrderBuilder:

    def __init__(self):
        self.reset()
    
    def reset(self):
        self.status = "pendiente"
        self.products = []
        return self
    
    def set_status(self, status):
        valid_statuses = ['pendiente', 'enviado']
        if status not in valid_statuses:
            raise ValueError(f"Estado inválido. Debe ser uno de: {valid_statuses}")
        self.status = status
        return self
    
    def set_products(self, products):
        self.products = products
        return self
    
    def add_product(self, product, quantity=1):
        self.products.append((product, quantity))
        return self
    
    def from_cart(self, cart: Dict[str, int]):
        if not cart:
            raise ValueError("El carrito está vacío")
        
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                self.add_product(product, quantity)
            except Product.DoesNotExist:
                raise ValueError(f"Producto con id {product_id} no existe")
        
        return self
    
    def build(self) -> Order:
        if len(self.products) == 0:
            raise ValueError("No se pueden crear órdenes sin productos")
        
        order = Order.objects.create(status=self.status)
        
        total = 0
        for item in self.products:
            if isinstance(item, tuple):
                product, quantity = item
            else:
                product = item
                quantity = 1
            
            OrderItemBuilder() \
                .set_order(order) \
                .set_product(product) \
                .set_quantity(quantity) \
                .build()
            
            total += product.price * quantity
        
        order.total = total
        order.save()
        
        self.reset()
        return order
