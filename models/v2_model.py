import pandas as pd
from models.model_utils import preprocess_data, recommend_routine

class V2Model:
    def __init__(self, shelf_data_path):
        self.shelf_data = pd.read_csv(shelf_data_path)
        self.shelf_data = preprocess_data(self.shelf_data)

    def recommend(self, user_preferences):
        return recommend_routine(self.shelf_data, user_preferences)

if __name__ == "__main__":
    model = V2Model('data/product_shelf.csv')
    user_prefs = {'category': 'Skincare', 'time_of_day': 'Morning'}
    recommendations = model.recommend(user_prefs)
    print(recommendations)
