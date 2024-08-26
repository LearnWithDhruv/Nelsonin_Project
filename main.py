from models.v2_model import V2Model
from models.v3_model import V3Model

def main():
    v2_model = V2Model('data/product_shelf.csv')
    v3_model = V3Model('data/product_catalogue.csv')

    user_preferences = {'category': 'Skincare', 'time_of_day': 'Morning'}

    v2_recommendations = v2_model.recommend(user_preferences)
    v3_recommendations = v3_model.recommend(user_preferences)

    print("V2 Recommendations:")
    print(v2_recommendations)

    print("V3 Recommendations:")
    print(v3_recommendations)

if __name__ == "__main__":
    main()
