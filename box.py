from product import Product

class Box:
    def __init__(self, box_id: int, wave_class: str):
        self.wave_class = wave_class
        self.products = []
        self.wave = None
        self.corridors: dict[str, set[str]] = {}
        self.id = box_id

    def add_product(self, sku: str, quantity: int):
        self.products.append(Product(sku, quantity))

    def set_wave(self, wave):
        self.wave = wave

    def add_corridor(self, corridor:str, product_sku: str):
        if corridor not in self.corridors:
            self.corridors[corridor] = set()
        self.corridors[corridor].add(product_sku)

    def find_product(self, sku: str):
        for product in self.products:
            if product.sku == sku:
                return product
        return None

    def get_total_products(self):
        return sum([product.quantity for product in self.products])

    def get_corridors(self):
        return self.corridors.keys()