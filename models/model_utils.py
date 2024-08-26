import pandas as pd

def preprocess_data(data):
    data['category'] = data['category'].str.lower()
    data['sub_category'] = data['sub_category'].str.lower()
    return data

def recommend_routine(data, user_preferences):
    filtered_data = data[
        (data['category'] == user_preferences['category'].lower()) 
        # (data['time_of_day'] == user_preferences['time_of_day'].lower())
    ]
    return filtered_data