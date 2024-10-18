import streamlit as st
import pandas as pd 
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pyrebase
from datetime import datetime
import functools
import requests
import random
from streamlit_option_menu import option_menu

# Firebase configuration
firebaseConfig = {
    'apiKey': "AIzaSyCZPtwe0V9lMRTqUEqDcPKFALHwlefAmho",
    'authDomain': "courserecsystem-9a84c.firebaseapp.com",
    'projectId': "courserecsystem-9a84c",
    'databaseURL': "https://courserecsystem-9a84c-default-rtdb.europe-west1.firebasedatabase.app/",
    'storageBucket': "courserecsystem-9a84c.appspot.com",
    'messagingSenderId': "149618883518",
    'appId': "1:149618883518:web:0d6c9b123973bf5e1cd7ef",
    'measurementId': "G-YCFDDD2VLR"
}

# Initialize Firebase
try:
    firebase = pyrebase.initialize_app(firebaseConfig)
    auth = firebase.auth()  
    db = firebase.database()
    storage = firebase.storage()
except Exception as e:
    st.error("Failed to initialize Firebase.")
    # Optionally log the exception to a file or monitoring tool here
    print(f"Firebase initialization error: {e}")

# Page config
st.set_page_config(initial_sidebar_state="collapsed")
query_params = st.query_params
user_id = query_params['user_id'][0] if 'user_id' in query_params else None

# Add custom CSS for UI styling
st.markdown(
    """
    <style>
    body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
    .header { text-align: center; color: purple; }
    .subheader { text-align: left; color: #b153ea; }
    .card { border: 1px solid #ccc; padding: 20px; border-radius: 10px; background-color: white; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); width: 550px; }
    .card:hover { border: 1px solid #a789b9; transform: scale(1.05); }
    .button { background-color: #b153ea; color: white; padding: 8px 16px; cursor: pointer; }
    </style>
    """, unsafe_allow_html=True
)

# Initialize session state for interested courses
if 'interested_courses' not in st.session_state:
    st.session_state.interested_courses = []

# Function to load CSV data
def load_data(data):
    try:
        df = pd.read_csv(data)
        return df
    except Exception as e:
        st.error("Error loading data.")
        print(f"Data loading error: {e}")
        return pd.DataFrame()  # Return an empty DataFrame as fallback

# Function to vectorize text to cosine similarity matrix
def vectorize_text_to_cosine_mat(data, title):
    try:
        count_vect = CountVectorizer()
        data.fillna("", inplace=True)
        cv_mat = count_vect.fit_transform(data['course_title'])
        cosine_sim_mat = cosine_similarity(cv_mat)
        return cosine_sim_mat
    except Exception as e:
        st.error("Error processing data for recommendations.")
        print(f"Vectorization error: {e}")
        return np.array([])  # Return an empty array as fallback

