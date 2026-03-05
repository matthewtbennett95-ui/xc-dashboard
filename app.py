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
conn = st.connection("gsheets", type=GSheetsConnection)
roster_data = conn.read(worksheet="Roster", ttl=0)
races_data = conn.read(worksheet="Races", ttl=0)

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["first_name"] = ""
    st.session_state["last_name"] = ""
    st.session_state["role"] = ""
    st.session_state["first_login"] = False

def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["first_name"] = ""
    st.session_state["last_name"] = ""
    st.session_state["role"] = ""
    st.session_state["first_login"] = False

# --- LOGIN PAGE ---
def login_page():
    st.title("MCXC Team Dashboard")
    st.markdown("Please log in to access your training data.")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Log In")
        
        if submit_button:
            user_row = roster_data[roster_data["Username"] == username]
            
            if not user_row.empty:
                correct_password = str(user_row.iloc[0]["Password"])
                
                if password == correct_password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["first_name"] = user_row.iloc[0]["First_Name"]
                    st.session_state["last_name"] = user_row.iloc[0]["Last_Name"]
                    st.session_state["role"] = user_row.iloc[0]["Role"]
                    
                    # --- THE ULTIMATE BULLETPROOF CHECK ---
                    raw_status = user_row.iloc[0]["First_Login"]
                    cleaned_status = str(raw_status).strip().upper()
                    
                    # Now it looks for TRUE, 1, or 1.0
                    if cleaned_status in ["TRUE", "1", "1.0"]:
                        st.session_state["first_login"] = True
                    else:
                        st.session_state["first_login"] = False
                    
                    st.rerun()
                    # --------------------------------------
                else:
                    st.error("Incorrect password. Please try again.")
            else:
                st.error("Username not found.")

# --- PASSWORD RESET PAGE ---
def password_reset_page():
    st.title("Welcome to the Team! 🏃")
    st.markdown("Since this is your first time logging in, please create a new, secure password.")
    
    with st.form("reset_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submit_reset = st.form_submit_button("Update Password")
        
        if submit_reset:
            if len(new_password) < 4:
                st.error("Password must be at least 4 characters long.")
            elif new_password != confirm_password:
                st.error("Passwords do not match. Try again!")
            else:
                # 1. Find the exact row for this user in the Roster dataframe
                user_index = roster_data.index[roster_data['Username'] == st.session_state['username']].tolist()[0]
                
                # 2. Update their password and change First_Login to FALSE
                roster_data.at[user_index, 'Password'] = new_password
                roster_data.at[user_index, 'First_Login'] = "FALSE"
                
                # 3. Push the entire updated dataframe back to Google Sheets
                with st.spinner("Updating your account securely..."):
                    conn.update(worksheet="Roster", data=roster_data)
                
                # 4. Clear the cache, update session state, and let them into the app
                st.cache_data.clear()
                st.session_state["first_login"] = False
                st.rerun()

# --- HOME PAGE (DASHBOARD) ---
def home_page():
    user_role = str(st.session_state["role"]).capitalize()
    first_name = st.session_state["first_name"]
    last_name = st.session_state["last_name"]
    
    st.title(f"{user_role}: {first_name} {last_name}")
    st.button("Log Out", on_click=logout)
    st.markdown("---")
    
    st.header("Race Results & Analytics")
    
    user_races = races_data[races_data["Username"] == st.session_state["username"]].copy()
    
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
        
        unique_distances = user_races["Distance"].unique()
        
        for dist in unique_distances:
            st.subheader(f"{dist} Races")
            dist_races = user_races[user_races["Distance"] == dist].copy()
            
            # Base columns
            display_cols = ["Date", "Meet_Name", "Mile_1"]
            if str(dist).upper() == "5K":
                display_cols.append("Mile_2")
                
            display_cols.extend(["Final_Kick", "Total_Time", "Avg_Pace"])
            
            # Dictionary to clean up the names for the user interface
            rename_dict = {
                "Meet_Name": "Meet Name",
                "Mile_1": "Mile 1",
                "Mile_2": "Mile 2",
                "Final_Kick": "Final Kick",
                "Total_Time": "Total Time",
                "Avg_Pace": "Avg Pace"
            }
            
            # Apply the clean names and display
            clean_table = dist_races[display_cols].rename(columns=rename_dict)
            st.dataframe(clean_table, hide_index=True, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
    else:
        st.info("No race data found yet for this season.")
        
# --- MAIN APP LOGIC ---
# The "Traffic Director" now has three routes!
if not st.session_state["logged_in"]:
    login_page()
elif st.session_state["first_login"]:
    password_reset_page()
else:
    home_page()
