import pandas as pd

def create_features(data):
    data['price_range'] = pd.cut(data['price'], bins=[0, 20, 50, 100, 200], labels=['Low', 'Medium', 'High', 'Premium'])
    return data

if __name__ == "__main__":
    data = pd.read_csv('data/preprocessed_catalogue.csv')
    data = create_features(data)
    data.to_csv('data/featured_catalogue.csv', index=False)
