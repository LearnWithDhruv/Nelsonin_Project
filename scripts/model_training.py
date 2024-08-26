import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from joblib import dump

def train_model(data_file, model_file):
    data = pd.read_csv(data_file)
    X = data.drop(columns=['product_id', 'product_name'])  
    y = data['category']  
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    
    dump(model, model_file)

if __name__ == "__main__":
    train_model('data/featured_catalogue.csv', 'models/product_model_v3.joblib')
