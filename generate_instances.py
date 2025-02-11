from random import random, randint

import numpy as np
import pandas as pd
import openpyxl


class GenerateInstances:
    def __init__(self, number_boxes, number_products, number_wave_class, number_corridors, number_corridors_floor, seed=42):
        self.number_boxes = number_boxes
        self.number_products = number_products
        self.wave_classes = [f"CLASSE_ONDA_{i + 1}" for i in range(number_wave_class)]
        self.boxes_ids = [box_id for box_id in range(1, number_boxes + 1)]
        self.corridors_ids = [corridor_id for corridor_id in range(1, number_corridors + 1)]
        self.products = [f"SKU_{i + 1}" for i in range(number_products)]
        self.seed = seed
        self.number_floors = -(-number_corridors // number_corridors_floor)
        self.column_box = self.generate_column_box()
        self.column_products = self.generate_column_products()
        self.column_number_products = self.generate_column_number_products()
        self.column_wave_class = self.generate_column_wave_class()
        self.column_corridor_products = self.generate_column_corridor_products()
        self.column_corridor_products_quantities = self.generate_column_corridor_products_quantities()
        self.column_corridor = self.generate_column_corridor()
        self.column_floor = self.generate_column_floor()
        # self.column_sku = self.generate_column_sku()
        # self.column_pieces = self.generate_column_pieces()


    def generate_column_box(self) -> np.array:
        column_box = np.array([])
        for box_id in self.boxes_ids:
            number_of_products = max(1, int(random() * self.number_products))
            column_box = np.concatenate((column_box, np.full(number_of_products, box_id)))
        return column_box

    def generate_column_products(self) -> np.array:
        column_products = np.array([])
        for i in range(len(self.column_box)):
            product = self.products[int(random() * self.number_products)]
            column_products = np.concatenate((column_products, np.array([product])))
        return column_products

    def generate_column_number_products(self) -> np.array:
        column_number_products = np.array([])
        numbers = np.arange(1, 51)

        # Define weights: smaller numbers have higher probabilities
        weights = 1 / numbers  # Inverse distribution (small numbers = higher prob)
        weights /= weights.sum()  # Normalize to sum = 1
        for i in range(len(self.column_box)):
            chosen_number = np.random.choice(numbers, p=weights)
            column_number_products = np.concatenate((column_number_products, np.array([chosen_number])))
        return column_number_products

    def generate_column_wave_class(self) -> np.array:
        column_wave_class = np.array([])
        current_box = self.column_box[0]
        wave_class = None
        for i, box in enumerate(self.column_box):
            if not wave_class or box != current_box:
                wave_class = self.wave_classes[int(random() * len(self.wave_classes))]
                current_box = box
            column_wave_class = np.concatenate((column_wave_class, np.array([wave_class])))
        return column_wave_class

    def generate_column_corridor(self) -> np.array:
        # Repeat corridor IDs to match the length of column_corridor_products
        return np.repeat(self.corridors_ids, len(self.column_corridor_products) // len(self.corridors_ids) + 1)[
               :len(self.column_corridor_products)]

    def generate_column_floor(self) -> np.array:
        # Repeat floor numbers to match the length of column_corridor_products
        floor_ids = np.repeat(
            [randint(1, self.number_floors) for _ in range(len(self.corridors_ids))],
            len(self.column_corridor_products) // len(self.corridors_ids) + 1
        )
        return floor_ids[:len(self.column_corridor_products)]

    # para gerar os produtos e quantidades, tenho que garantir que os corredores
    # atendam as demandas das caixas, minimamente a demanda das caixas

    def generate_column_corridor_products(self) -> np.array:
        # Calculate total demand for each product from box demands
        product_demand = {product: 0 for product in self.products}
        for product, quantity in zip(self.column_products, self.column_number_products):
            product_demand[product] += quantity

        # Distribute products to corridors
        column_corridor_products = []
        corridors = self.corridors_ids

        for product, total_demand in product_demand.items():
            # Divide the product demand across the corridors
            assigned_corridors = np.random.choice(corridors, size=len(corridors), replace=False)
            for corridor in assigned_corridors:
                if total_demand <= 0:
                    break
                # Assign a portion of the demand to this corridor
                supply = min(total_demand, randint(1, 10))
                column_corridor_products.append((corridor, product))
                total_demand -= supply

        # Group by corridors and return as array
        return np.array([product for corridor, product in sorted(column_corridor_products)])

    def generate_column_corridor_products_quantities(self) -> np.array:
        # Calculate total demand for each product
        product_demand = {product: 0 for product in self.products}
        for product, quantity in zip(self.column_products, self.column_number_products):
            product_demand[product] += quantity

        # Distribute product quantities across corridors
        column_corridor_products_quantities = []
        corridors = self.corridors_ids

        for product, total_demand in product_demand.items():
            assigned_corridors = np.random.choice(corridors, size=len(corridors), replace=False)
            for corridor in assigned_corridors:
                if total_demand <= 0:
                    break
                # Assign a portion of the demand to this corridor
                supply = min(total_demand, randint(1, 10))
                column_corridor_products_quantities.append((corridor, product, supply))
                total_demand -= supply

        # Return quantities as array, grouped by corridors
        return np.array([supply for corridor, product, supply in sorted(column_corridor_products_quantities)])

    def stock(self):
        return self.column_floor, self.column_corridor, self.column_corridor_products, self.column_corridor_products_quantities

    def box(self):
        return self.column_box,self.column_number_products,  self.column_wave_class, self.column_products

    def box_to_csv(self):
        box = self.box()
        df = pd.DataFrame({
            "CAIXA": box[0],
            "PECAS": box[1],
            "CLASSE_ONDA": box[2],
            "SKU": box[3]
        })
        df.to_csv("box.csv", index=False)

    def stock_to_csv(self):
        stock = self.stock()
        df = pd.DataFrame({
            "ANDAR": stock[0],
            "CORREDOR": stock[1],
            "SKU": stock[2],
            "PECAS": stock[3]
        })
        df.to_csv("stock.csv", index=False)

    def generate_excel(self):
        stock = self.stock()
        box = self.box()
        with pd.ExcelWriter('instances.xlsx') as writer:
            df_stock = pd.DataFrame({
                "ANDAR": stock[0],
                "CORREDOR": stock[1],
                "SKU": stock[2],
                "PECAS": stock[3]
            })
            df_stock.to_excel(writer, sheet_name='Estoque', index=False)
            df_box = pd.DataFrame({
                "CAIXA": box[0],
                "PECAS": box[1],
                "CLASSE_ONDA": box[2],
                "SKU": box[3]
            })
            df_box.to_excel(writer, sheet_name='Caixas', index=False)


if __name__ == "__main__":
    instances = GenerateInstances(10, 5, 3, 5, 2)
    print(instances.column_box)
    print(instances.column_products)
    print(instances.column_number_products)
    print(instances.column_wave_class)
    print(instances.column_corridor)
    print(len(instances.column_corridor))
    print(instances.column_floor)
    print(len(instances.column_floor))
    print(instances.column_corridor_products)
    print(len(instances.column_corridor_products))
    print(instances.column_corridor_products_quantities)
    print(len(instances.column_corridor_products_quantities))
    instances.box_to_csv()
    instances.stock_to_csv()
    instances.generate_excel()
