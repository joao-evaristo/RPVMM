from csv_reader import CSVReader

if __name__ == "__main__":
    stock_layout = {
        "floor": [],
        "corridor": [],
        "sku": [],
        "pieces": []
    }
    product_boxes = {
        "wave_id": [],
        "box_id": [],
        "box_pieces": [],
        "wave_class": [],
        "product_boxes_sku": []
    }
    stock_layout_file = CSVReader("stock_layout_1.csv")
    stock_layout["floor"] = stock_layout_file.get_column_values("ANDAR")
    stock_layout["corridor"] = stock_layout_file.get_column_values("CORREDOR")
    stock_layout["sku"] = stock_layout_file.get_column_values("SKU")
    stock_layout["pieces"] = stock_layout_file.get_column_values("PECAS")

    product_boxes_file = CSVReader("product_boxes_1.csv")
    product_boxes["wave_id"] = product_boxes_file.get_column_values("ONDA_ID")
    product_boxes["box_id"] = product_boxes_file.get_column_values("CAIXA_ID")
    product_boxes["box_pieces"] = product_boxes_file.get_column_values("PECAS")
    product_boxes["wave_class"] = product_boxes_file.get_column_values("CLASSE_ONDA")
    product_boxes["product_boxes_sku"] = product_boxes_file.get_column_values("SKU")