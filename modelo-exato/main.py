from csv_reader import CSVReader
from test_gurobi import resolve_modelo

if __name__ == "__main__":
    stock_layout_file = CSVReader("stock_layout_1.csv")
    sku_stock = stock_layout_file.get_column_values("SKU")
    corredor_stock = stock_layout_file.get_column_values("CORREDOR")
    andar_stock = stock_layout_file.get_column_values("ANDAR")
    pecas_stock = stock_layout_file.get_column_values("PECAS")

    data_q = {
        (sku, corredor, andar): pecas
        for sku, corredor, andar, pecas in zip(sku_stock, corredor_stock, andar_stock, pecas_stock)
    }

    product_boxes_file = CSVReader("product_boxes_1.csv")
    sku_boxes = product_boxes_file.get_column_values("SKU")
    caixa_id_boxes = product_boxes_file.get_column_values("CAIXA_ID")
    pecas_boxes = product_boxes_file.get_column_values("PECAS")
    onda_boxes = product_boxes_file.get_column_values("ONDA_ID")
    classe_onda_boxes = product_boxes_file.get_column_values("CLASSE_ONDA")

    P = list(set(sku_stock))
    K = list(set(corredor_stock))
    A = list(set(andar_stock))
    I = list(set(caixa_id_boxes))
    J = list(set(onda_boxes))
    C = list(set(classe_onda_boxes))

    q_pi_input = {
        (sku, caixa_id): pecas
        for sku, caixa_id, pecas in zip(sku_boxes, caixa_id_boxes, pecas_boxes)
    }

    resolve_modelo(P, K, A, I, J, C, data_q, q_pi_input)

