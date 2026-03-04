import streamlit as st
import pandas as pd

# --- PAGE SETUP ---
# This configures the browser tab title and layout
st.set_page_config(page_title="XC Team Hub", page_icon="🏃‍♂️", layout="centered")

# --- MOCK DATA ---
# A temporary dictionary of usernames and passwords. 
# Later, we will connect this to your "Roster" Google Sheet tab.
MOCK_USERS = {"runner1": "xc2026", "fastkid": "pace123"}

# --- SESSION STATE INITIALIZATION ---
# This tells the app to remember if someone is logged in across page refreshes
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

# --- LOGIN PAGE ---
def login_page():
    st.title("🏃‍♂️ XC Team Hub")
    st.markdown("Welcome! Please log in to see your training dashboard.")
    
    # A form groups the inputs together so it only processes when they hit "Log In"
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Log In")
        
        if submit_button:
            if username in MOCK_USERS and MOCK_USERS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun() # Refreshes the app to load the dashboard
            else:
                st.error("Incorrect username or password. Try again!")

# --- HOME PAGE (DASHBOARD) ---
def home_page():
    # A personalized greeting
    st.title(f"Welcome back, {st.session_state['username']}! 🏅")
    st.button("Log Out", on_click=logout)
    
    st.markdown("---")
    
    # Section 1: Suggested Paces & Quick Stats
    st.header("🎯 Today's Target")
    
    # Columns let us put data side-by-side
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Current 5K PR", value="16:45", delta="-0:12") # The delta shows improvement!
    with col2:
        st.metric(label="Suggested Interval Pace (400m)", value="72s")
        
    st.markdown("---")
    
    # Section 2: Recent Workouts
    st.header("📊 Recent Workouts")
    
    # Mock data table for visual purposes
    workout_data = pd.DataFrame({
        "Date": ["Oct 10", "Oct 12", "Oct 15"],
        "Workout": ["6x800m", "4 Mile Tempo", "8x400m"],
        "Weather": ["65°F, Sunny", "55°F, Rain", "60°F, Overcast"],
        "Avg Split": ["2:25", "5:45/mi", "71s"]
    })
    
    # Display the table cleanly
    st.dataframe(workout_data, hide_index=True, use_container_width=True)

# --- MAIN APP LOGIC ---
# This simple if/else acts as our "traffic director"
if not st.session_state["logged_in"]:
    login_page()
else:
    home_page()
