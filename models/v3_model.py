import pandas as pd
from models.model_utils import preprocess_data, recommend_routine

class V3Model:
    def __init__(self, catalogue_data_path):
        self.catalogue_data = pd.read_csv(catalogue_data_path)
        self.catalogue_data = preprocess_data(self.catalogue_data)

    def recommend(self, user_preferences):
        return recommend_routine(self.catalogue_data, user_preferences)

if __name__ == "__main__":
    model = V3Model('data/product_catalogue.csv')
    user_prefs = {'category': 'Skincare', 'time_of_day': 'Morning'}
    recommendations = model.recommend(user_prefs)
    print(recommendations)
