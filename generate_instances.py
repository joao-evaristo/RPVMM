from random import random, randint, choice

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
        self.product_demand = dict(zip(self.products, [0 for _ in range(number_products)]))
        self.seed = seed
        self.number_floors = -(-number_corridors // number_corridors_floor)
        self.column_box = self.generate_column_box()
        self.column_products = self.generate_column_products()
        self.column_number_products = self.generate_column_number_products()
        self.column_wave_class = self.generate_column_wave_class()
        self.column_corridor = self.generate_column_corridor()
        self.column_floor = self.generate_column_floor()
        self.column_corridor_products, self.column_corridor_products_quantities = self.generate_column_corridor_products()
        self.ensure_product_demand_met()

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
            self.product_demand[self.column_products[i]] += chosen_number
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
        column_corridor = np.array([])
        for i in range(len(self.corridors_ids)):
            corridor_repeat = random() * 10
            column_corridor = np.concatenate((column_corridor, np.full(int(corridor_repeat), self.corridors_ids[i])))
        return column_corridor

    def generate_column_floor(self) -> np.array:
        column_corridor_floor = np.array([])
        actual_floor = 1
        actual_corridor = self.column_corridor[0]
        for i, corridor in enumerate(self.column_corridor):
            if corridor != actual_corridor:
                actual_floor = randint(1, self.number_floors)
                actual_corridor = corridor
            column_corridor_floor = np.concatenate((column_corridor_floor, np.array([actual_floor])))
        return column_corridor_floor


    def generate_column_corridor_products(self) -> np.array:
        column_corridor_products = np.array([])
        column_corridor_products_quantities = np.array([])
        current_corridor = self.column_corridor[0]
        corridor_products = []
        for i, corridor in enumerate(self.column_corridor):
            if corridor != current_corridor:
                corridor_products.clear()
            products_with_demand = list(self.product_demand.keys())
            possible_products = list(set(products_with_demand) - set(corridor_products))
            if not possible_products:
                product = self.products[int(random() * len(corridor_products))]
            else:
                product = possible_products[int(random() * len(possible_products))]
            corridor_products.append(product)
            quantity = randint(1, 500)
            self.product_demand[product] -= quantity
            if self.product_demand[product] <= 0:
                products_with_demand.remove(product)
            column_corridor_products = np.concatenate((column_corridor_products, np.array([product])))
            column_corridor_products_quantities = np.concatenate((column_corridor_products_quantities, np.array([quantity])))
        return column_corridor_products, column_corridor_products_quantities

    def ensure_product_demand_met(self):
        for product, demand in self.product_demand.items():
            if demand > 0:
                corridors_with_product = [
                    (idx, corridor)
                    for idx, corridor in enumerate(self.column_corridor_products)
                    if corridor == product
                ]

                if corridors_with_product:
                    chosen_idx, chosen_corridor = choice(corridors_with_product)

                    self.column_corridor_products_quantities[chosen_idx] += demand
                    self.product_demand[product] = 0

                    print(f"Ajustado: {product} no corredor {chosen_corridor} (+{demand})")
                else:
                    print(f"Atenção! Nenhum corredor disponível para atender {product}.")

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
    instances = GenerateInstances(2000, 2000, 6, 165, 5)
    instances.box_to_csv()
    instances.stock_to_csv()
    instances.generate_excel()
