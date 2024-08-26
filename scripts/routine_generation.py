import pandas as pd
from joblib import load

def generate_routines(model_file, input_data, routine_file):
    model = load(model_file)
    predictions = model.predict(input_data)
    
    routines = pd.DataFrame({'product_id': input_data['product_id'], 'predicted_category': predictions})
    routines.to_csv(routine_file, index=False)

if __name__ == "__main__":
    input_data = pd.read_csv('data/featured_catalogue.csv')
    generate_routines('models/product_model_v3.joblib', input_data, 'data/generated_routines.csv')
