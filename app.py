import streamlit as st
import pandas as pd

# --- PAGE SETUP ---
st.set_page_config(page_title="MCXC Team Dashboard", layout="centered")

# --- CUSTOM CSS FOR SCHOOL COLORS ---
# This adds a sleek color bar at the top with your school colors
st.markdown("""
    <style>
        .color-bar {
            height: 8px;
            background: linear-gradient(to right, #8B2331, #0C223F, #C7B683);
            margin-bottom: 2rem;
            border-radius: 4px;
        }
    </style>
    <div class="color-bar"></div>
""", unsafe_allow_html=True)

# --- MOCK DATA ---
MOCK_USERS = {"runner1": "xc2026", "fastkid": "pace123"}

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

# --- LOGIN PAGE ---
def login_page():
    st.title("MCXC Team Dashboard")
    st.markdown("Please log in to access your training data.")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Log In")
        
        if submit_button:
            if username in MOCK_USERS and MOCK_USERS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Incorrect username or password. Please try again.")

# --- HOME PAGE (DASHBOARD) ---
def home_page():
    st.title(f"Athlete: {st.session_state['username'].upper()}")
    st.button("Log Out", on_click=logout)
    
    st.markdown("---")
    
    # Section 1: Suggested Paces & Quick Stats
    st.header("Today's Target")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Current 5K PR", value="16:45", delta="-0:12")
    with col2:
        st.metric(label="Suggested Interval Pace (400m)", value="72s")
        
    st.markdown("---")
    
    # Section 2: Recent Workouts
    st.header("Recent Workouts")
    
    workout_data = pd.DataFrame({
        "Date": ["Oct 10", "Oct 12", "Oct 15"],
        "Workout": ["6x800m", "4 Mile Tempo", "8x400m"],
        "Weather": ["65°F, Sunny", "55°F, Rain", "60°F, Overcast"],
        "Avg Split": ["2:25", "5:45/mi", "71s"]
    })
    
    st.dataframe(workout_data, hide_index=True, use_container_width=True)

# --- MAIN APP LOGIC ---
if not st.session_state["logged_in"]:
    login_page()
else:
    home_page()
