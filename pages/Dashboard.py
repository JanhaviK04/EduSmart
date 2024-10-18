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

# Function to get recommendations
def get_recommendation(title, cosine_sim_mat, df, num_of_rec=10):
    try:
        specific_course_index = df[df['course_title'] == title].index[0]
        sim_scores = cosine_sim_mat[specific_course_index]
        sorted_indices = np.argsort(sim_scores)[::-1]
        recommended_indices = [idx for idx in sorted_indices if idx != specific_course_index]
        recommended_courses = df.iloc[recommended_indices]
        return recommended_courses.head(num_of_rec)
    except Exception as e:
        st.error("Error fetching recommendations.")
        print(f"Recommendation error: {e}")
        return pd.DataFrame()  # Return empty DataFrame as fallback

# Cache search function
@st.cache_data
def search_term_if_not_found(search_term, df):
    try:
        search_results = df[df['subject'].str.contains(search_term, case=False) | df['course_title'].str.contains(search_term, case=False)]
        return search_results
    except Exception as e:
        st.error("Error searching for the term.")
        print(f"Search error: {e}")
        return pd.DataFrame()

# Function to log course history in Firebase
def fb(course_title):     
    try:
        db.child('history').push({
            "user_id": user_id,
            "course_title": course_title
        })
    except Exception as e:
        print(f"Firebase write error: {e}")

# Interested button click function
def on_interested_button_click(course_title):
    try:
        st.session_state.interested_courses.append(course_title)
        fb(course_title)
    except Exception as e:
        st.error("Error adding course to interested list.")
        print(f"Button click error: {e}")

# Display course cards
def display_course_cards(data):
    try:
        for idx, row in data.iterrows():
            st.markdown(
                f"""
                <div class="card">
                    <div class="thumbnail">
                        <img src="{row['img']}" alt="Thumbnail">
                    </div>
                    <h3>{row['course_title']}</h3>
                    <p><strong>Link:</strong> <a href="{row['url']}">{row['url']}</a></p>
                    <p><strong>Is paid?:</strong> {row['is_paid']}</p>
                    <p><strong>Level:</strong> {row['level']}</p>
                    <p><strong>Subject:</strong> {row['subject']}</p>
                    <p><strong>Language:</strong> {row['language']}</p>
                </div>
                """, unsafe_allow_html=True
            )
            button_key = f"interested_button_{idx}_{random.randint(1, 100000)}"
            on_click = functools.partial(on_interested_button_click, row['course_title'])
            st.button('Interested', key=button_key, on_click=on_click)
            st.write("----")
    except Exception as e:
        st.error("Error displaying course cards.")
        print(f"Display card error: {e}")

# Main app function
def app():
    st.markdown("<h1 style='text-align: center; color: #6f07bb;'>EduSmart </h1>", unsafe_allow_html=True)
    
    choice = option_menu(None, ["Home", "Search"], icons=['house','search'], orientation='horizontal')
   
    df = load_data("data/course_data.csv")
    
    if choice == "Home":
        st.markdown("<h3 style='text-align: left; color: #b153ea;'>Recommended Courses:</h>", unsafe_allow_html=True)
        if user_id:
            try:
                url = f"{firebaseConfig['databaseURL']}/history.json"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    course_titles = [value["course_title"] for key, value in data.items() if "user_id" in value and value["user_id"] == user_id]
                    if course_titles:
                        for title in course_titles:
                            cosine_sim_mat = vectorize_text_to_cosine_mat(df, title)   
                            recommendations = get_recommendation(title, cosine_sim_mat, df, 5)
                            display_course_cards(recommendations)
                    else:
                        st.write("No course titles found for user_id:", user_id)
                else:
                    st.error("Failed to retrieve data from Firebase.")
            except Exception as e:
                st.error("Error retrieving user data.")
                print(f"Home page error: {e}")
    
    if choice == "Search":
        st.markdown("<h3 style='text-align: left; color: purple;'>Search for courses</h>", unsafe_allow_html=True)
        search_term = st.text_input("Search")
        if st.button("Search"):
            if search_term:
                try:
                    st.info("Suggested Options include")
                    result_df = search_term_if_not_found(search_term, df)
                    display_course_cards(result_df)
                except Exception as e:
                    st.error("Error processing search.")
                    print(f"Search page error: {e}")

if name == 'main':
    app()
