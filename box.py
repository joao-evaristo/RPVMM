from product import Product

class Box:
    def __init__(self, wave_class: str):
        self.wave_class = wave_class
        self.products = []
        self.wave = None
        self.corridors = set()

    def add_product(self, sku: str, quantity: int):
        self.products.append(Product(sku, quantity))

    def set_wave(self, wave):
        self.wave = wave

    def add_corridor(self, corridor):
        self.corridors.add(corridor)

    def find_product(self, sku: str):
        for product in self.products:
            if product.sku == sku:
                return product
        return None

    def get_total_products(self):
        return sum([product.quantity for product in self.products])