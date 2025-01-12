from product import Product

class Box:
    def __init__(self, wave_class: str):
        self.wave_class = wave_class
        self.products = []
        self.wave = None
        self.corridors = []

    def add_product(self, sku: str, quantity: int):
        self.products.append(Product(sku, quantity))

    def set_wave(self, wave):
        self.wave = wave

    def add_corridor(self, corridor):
        self.corridors.append(corridor)

    def find_product(self, sku: str):
        """Search for a product by SKU in the box."""
        for product in self.products:
            if product.sku == sku:
                return product
        return None  # Return None if the product is not found

