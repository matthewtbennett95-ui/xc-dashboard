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

# Make sure the Active column is treated as a string for easy filtering
if "Active" in roster_data.columns:
    roster_data["Active_Clean"] = roster_data["Active"].astype(str).str.strip().str.upper()
else:
    # Failsafe just in case the column isn't added yet
    roster_data["Active_Clean"] = "TRUE"

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

# --- HELPER FUNCTION: DRAW RACE TABLES ---
def display_athlete_races(target_username):
    user_races = races_data[races_data["Username"] == target_username].copy()
    
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
            
            display_cols = ["Date", "Meet_Name", "Mile_1"]
            if str(dist).upper() == "5K":
                display_cols.append("Mile_2")
                
            display_cols.extend(["Final_Kick", "Total_Time", "Avg_Pace"])
            
            rename_dict = {
                "Meet_Name": "Meet Name",
                "Mile_1": "Mile 1",
                "Mile_2": "Mile 2",
                "Final_Kick": "Final Kick",
                "Total_Time": "Total Time",
                "Avg_Pace": "Avg Pace"
            }
            
            clean_table = dist_races[display_cols].rename(columns=rename_dict)
            st.dataframe(clean_table, hide_index=True, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
    else:
        st.info("No race data found yet for this season.")

# --- LOGIN & PASSWORD RESET PAGES ---
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
                
                # Check if they are active!
                is_active = str(user_row.iloc[0].get("Active", "TRUE")).strip().upper() in ["TRUE", "1", "1.0"]
                
                if not is_active:
                    st.error("This account is no longer active.")
                elif password == correct_password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["first_name"] = user_row.iloc[0]["First_Name"]
                    st.session_state["last_name"] = user_row.iloc[0]["Last_Name"]
                    st.session_state["role"] = user_row.iloc[0]["Role"]
                    
                    raw_status = user_row.iloc[0]["First_Login"]
                    cleaned_status = str(raw_status).strip().upper()
                    if cleaned_status in ["TRUE", "1", "1.0"]:
                        st.session_state["first_login"] = True
                    else:
                        st.session_state["first_login"] = False
                    
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
            else:
                st.error("Username not found.")

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
                user_index = roster_data.index[roster_data['Username'] == st.session_state['username']].tolist()[0]
                roster_data.at[user_index, 'Password'] = new_password
                roster_data.at[user_index, 'First_Login'] = "FALSE"
                
                # Drop our temporary cleaning column before pushing to Google Sheets
                if "Active_Clean" in roster_data.columns:
                    push_data = roster_data.drop(columns=["Active_Clean"])
                else:
                    push_data = roster_data

                with st.spinner("Updating your account securely..."):
                    conn.update(worksheet="Roster", data=push_data)
                
                st.cache_data.clear()
                st.session_state["first_login"] = False
                st.rerun()

# --- HOME PAGE (DASHBOARD ROUTER) ---
def home_page():
    user_role = str(st.session_state["role"]).capitalize()
    first_name = st.session_state["first_name"]
    last_name = st.session_state["last_name"]
    
    st.title(f"{user_role}: {first_name} {last_name}")
    st.button("Log Out", on_click=logout)
    st.markdown("---")
    
    # --- ROUTE 1: COACH DASHBOARD ---
    if user_role.upper() == "COACH":
        tab1, tab2, tab3 = st.tabs(["Athlete Lookup", "Roster Management", "Add Race Data"])
        
        with tab1:
            st.subheader("Athlete Lookup")
            # Only show ACTIVE athletes in the lookup
            active_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE") & 
                                          (roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"]))]
            
            athlete_dict = {row["Username"]: f"{row['First_Name']} {row['Last_Name']}" for _, row in active_athletes.iterrows()}
            
            selected_username = st.selectbox("Select an Athlete:", options=list(athlete_dict.keys()), format_func=lambda x: athlete_dict[x])
            
            if selected_username:
                st.markdown(f"**Viewing data for: {athlete_dict[selected_username]}**")
                display_athlete_races(selected_username)
                
        with tab2:
            st.subheader("Roster Management")
            
            # Create a mini-menu inside the Roster tab
            roster_action = st.radio("Choose an action:", ["View Roster", "Add New Member", "Archive/Remove Member"], horizontal=True)
            st.markdown("---")
            
            if roster_action == "View Roster":
                active_roster = roster_data[roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"])].copy()
                
                # If Grad_Year exists, let them sort by it
                if "Grad_Year" in active_roster.columns:
                    # Clean up the display dataframe
                    display_roster = active_roster[["First_Name", "Last_Name", "Grad_Year", "Role", "Username"]].copy()
                    display_roster["Grad_Year"] = pd.to_numeric(display_roster["Grad_Year"], errors="coerce").fillna(0).astype(int)
                    # Convert 0s back to blank strings for a cleaner look
                    display_roster["Grad_Year"] = display_roster["Grad_Year"].replace(0, "")
                    
                    st.dataframe(display_roster.sort_values(by=["Grad_Year", "Last_Name"]), hide_index=True, use_container_width=True)
                else:
                    display_roster = active_roster[["First_Name", "Last_Name", "Role", "Username"]].copy()
                    st.dataframe(display_roster.sort_values(by=["Last_Name"]), hide_index=True, use_container_width=True)

            elif roster_action == "Add New Member":
                with st.form("add_member_form"):
                    col1, col2 = st.columns(2)
                    new_first = col1.text_input("First Name")
                    new_last = col2.text_input("Last Name")
                    new_grad_year = col1.text_input("Graduation Year (e.g., 2026)")
                    new_role = col2.selectbox("Role", ["Athlete", "Coach"])
                    
                    submit_new = st.form_submit_button("Add to Roster")
                    
                    if submit_new and new_first and new_last:
                        generated_username = f"{new_first.lower()}.{new_last.lower()}".replace(" ", "")
                        
                        # Create a new row of data
                        new_row = pd.DataFrame([{
                            "Username": generated_username,
                            "Password": "changeme", # Default temporary password
                            "First_Name": new_first,
                            "Last_Name": new_last,
                            "Role": new_role,
                            "First_Login": "TRUE",
                            "Active": "TRUE",
                            "Grad_Year": new_grad_year
                        }])
                        
                        # Drop the temporary clean column before updating
                        push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                        updated_roster = pd.concat([push_data, new_row], ignore_index=True)
                        
                        with st.spinner("Adding new member..."):
                            conn.update(worksheet="Roster", data=updated_roster)
                        
                        st.success(f"Added {new_first} {new_last}! Their username is '{generated_username}' and temporary password is 'changeme'.")
                        st.cache_data.clear()
                        st.rerun()

            elif roster_action == "Archive/Remove Member":
                st.warning("Archiving a runner hides them from the active roster and prevents them from logging in, but keeps their historical race data safe.")
                
                active_athletes = roster_data[roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"])]
                archive_dict = {row["Username"]: f"{row['First_Name']} {row['Last_Name']} ({row.get('Grad_Year', 'N/A')})" for _, row in active_athletes.iterrows()}
                
                user_to_archive = st.selectbox("Select Member to Archive:", options=list(archive_dict.keys()), format_func=lambda x: archive_dict[x])
                
                if st.button("Archive Member"):
                    user_index = roster_data.index[roster_data['Username'] == user_to_archive].tolist()[0]
                    roster_data.at[user_index, 'Active'] = "FALSE"
                    
                    push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                    
                    with st.spinner("Archiving member..."):
                        conn.update(worksheet="Roster", data=push_data)
                        
                    st.success("Member archived successfully.")
                    st.cache_data.clear()
                    st.rerun()

        with tab3:
            st.subheader("Data Entry Command Center")
            st.info("Coming soon: A secure form to add new race times directly to the Google Sheet without ever leaving this app.")

    # --- ROUTE 2: ATHLETE DASHBOARD ---
    else:
        st.header("Race Results & Analytics")
        display_athlete_races(st.session_state["username"])

# --- MAIN APP LOGIC ---
if not st.session_state["logged_in"]:
    login_page()
elif st.session_state["first_login"]:
    password_reset_page()
else:
    home_page()
