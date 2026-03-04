import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- PAGE SETUP & CSS ---
st.set_page_config(page_title="MCXC Team Dashboard", layout="centered")

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

# --- TIME MATH FUNCTIONS ---
def time_to_seconds(time_str):
    if pd.isna(time_str) or time_str == "" or ":" not in str(time_str):
        return 0
    parts = str(time_str).split(':')
    return int(parts[0]) * 60 + float(parts[1])

def seconds_to_time(seconds):
    if seconds <= 0:
        return ""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"

# --- SECURE DATABASE CONNECTION ---
# This tells Streamlit to log into Google Sheets using our hidden secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the tabs from the Google Sheet
# ttl=0 means the app fetches fresh data every time, so you see updates instantly
roster_data = conn.read(worksheet="Roster", ttl=0)
races_data = conn.read(worksheet="Races", ttl=0)

# --- SESSION STATE ---
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
            # Check if the username exists in the Roster sheet
            user_row = roster_data[roster_data["Username"] == username]
            
            if not user_row.empty:
                # Get the correct password from the sheet
                correct_password = str(user_row.iloc[0]["Password"])
                
                if password == correct_password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
            else:
                st.error("Username not found.")

# --- HOME PAGE (DASHBOARD) ---
def home_page():
    st.title(f"Athlete: {st.session_state['username'].upper()}")
    st.button("Log Out", on_click=logout)
    st.markdown("---")
    
    st.header("Race Results & Analytics")
    
    # Filter the races for ONLY the logged-in user
    user_races = races_data[races_data["Username"] == st.session_state["username"]].copy()
    
    # If they have race data, calculate the math and display it
    if not user_races.empty:
        def calculate_avg_pace(row):
            total_sec = time_to_seconds(row["Total_Time"])
            distance_mi = 3.10686 if str(row["Distance"]).upper() == "5K" else 2.0
            if total_sec == 0: return ""
            return seconds_to_time(total_sec / distance_mi)
            
        def calculate_kick(row):
            total_sec = time_to_seconds(row["Total_Time"])
            m1_sec = time_to_seconds(row["Mile_1"])
            m2_sec = time_to_seconds(row["Mile_2"])
            if total_sec == 0: return ""
            return seconds_to_time(total_sec - (m1_sec + m2_sec))
            
        user_races["Avg_Pace"] = user_races.apply(calculate_avg_pace, axis=1)
        user_races["Final_Kick"] = user_races.apply(calculate_kick, axis=1)
        
        display_cols = ["Date", "Meet_Name", "Distance", "Mile_1", "Mile_2", "Final_Kick", "Total_Time", "Avg_Pace"]
        
        # Display the table
        st.dataframe(user_races[display_cols], hide_index=True, use_container_width=True)
    else:
        st.info("No race data found yet for this season.")

# --- MAIN APP LOGIC ---
if not st.session_state["logged_in"]:
    login_page()
else:
    home_page()
