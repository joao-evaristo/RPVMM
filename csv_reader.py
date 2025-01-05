import pandas as pd


class CSVReader:
    def __init__(self, file):
        self.df = pd.read_csv(file)

    def get_column_values(self, column):
        df_column =  self.df[column]
        column_array = df_column.to_numpy()
        return column_array


# df1 = pd.read_csv("file1.csv")

# # Read the second CSV file
# df2 = pd.read_csv("file2.csv")
