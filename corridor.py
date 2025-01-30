from product import Product

class Corridor:
    def __init__(self, floor: int):
        self.floor = floor
        self.products = []
        self.waves = []

    def add_product(self, sku: str, quantity: int):
        self.products.append(Product(sku, quantity))

    def find_product(self, sku: str):
        """Search for a product by SKU in the box."""
        for product in self.products:
            if product.sku == sku:
                return product
        return None

    def add_wave(self, wave):
        self.waves.append(wave)

    def consume_product(self, sku: str, quantity: int):
        """Remove a product from the corridor."""
        for product in self.products:
            print(product.sku, product.quantity)
            print(sku)
            if product.sku == sku:
                if quantity >= product.quantity:
                    remaining = quantity - product.quantity
                    self.products.remove(product)
                else:
                    remaining = 0
                    product.quantity -= quantity
                return remaining
