import pandas as pd

def preprocess_data(input_file, output_file):
    data = pd.read_csv(input_file)
    data.to_csv(output_file, index=False)

if __name__ == "__main__":
    preprocess_data('data/product_catalogue.csv', 'data/preprocessed_catalogue.csv')
