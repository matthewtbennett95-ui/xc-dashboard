import streamlit as st
import pandas as pd
import datetime
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

# --- MATH & LOGIC FUNCTIONS ---
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

def get_grade_level(grad_year_str):
    if str(grad_year_str).upper() == "COACH" or not str(grad_year_str).strip().isdigit():
        return "Coach"
    
    grad_year = int(grad_year_str)
    today = datetime.date.today()
    
    # XC Season logic: Fall sport. If month < July, season was last year.
    current_season_year = today.year - 1 if today.month < 7 else today.year
    spring_grad_year = current_season_year + 1
    
    grade = 12 - (grad_year - spring_grad_year)
    
    if grade == 9: return "9th"
    elif grade == 10: return "10th"
    elif grade == 11: return "11th"
    elif grade == 12: return "12th"
    elif grade < 9: return "Middle School"
    elif grade > 12: return "Alumni"
    else: return "Unknown"

# --- SECURE DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)
roster_data = conn.read(worksheet="Roster", ttl=0)
races_data = conn.read(worksheet="Races", ttl=0)

# Failsafes for new columns in case they aren't filled out yet
if "Active" in roster_data.columns:
    roster_data["Active_Clean"] = roster_data["Active"].astype(str).str.strip().str.upper()
else:
    roster_data["Active_Clean"] = "TRUE"
    
if "Gender" not in roster_data.columns:
    roster_data["Gender"] = "N/A"

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["first_name"] = ""
    st.session_state["last_name"] = ""
    st.session_state["role"] = ""
    st.session_state["first_login"] = False

def logout():
    for key in ["logged_in", "username", "first_name", "last_name", "role", "first_login"]:
        st.session_state[key] = False if key in ["logged_in", "first_login"] else ""

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
            
            rename_dict = {"Meet_Name": "Meet Name", "Mile_1": "Mile 1", "Mile_2": "Mile 2", 
                           "Final_Kick": "Final Kick", "Total_Time": "Total Time", "Avg_Pace": "Avg Pace"}
            
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
        if st.form_submit_button("Log In"):
            user_row = roster_data[roster_data["Username"] == username]
            if not user_row.empty:
                is_active = str(user_row.iloc[0].get("Active", "TRUE")).strip().upper() in ["TRUE", "1", "1.0"]
                if not is_active:
                    st.error("This account is no longer active.")
                elif password == str(user_row.iloc[0]["Password"]):
                    st.session_state.update({
                        "logged_in": True, "username": username,
                        "first_name": user_row.iloc[0]["First_Name"], "last_name": user_row.iloc[0]["Last_Name"],
                        "role": user_row.iloc[0]["Role"]
                    })
                    cleaned_status = str(user_row.iloc[0]["First_Login"]).strip().upper()
                    st.session_state["first_login"] = cleaned_status in ["TRUE", "1", "1.0"]
                    st.rerun()
                else: st.error("Incorrect password.")
            else: st.error("Username not found.")

def password_reset_page():
    st.title("Welcome to the Team! 🏃")
    st.markdown("Since this is your first time logging in, please create a new, secure password.")
    with st.form("reset_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password"):
            if len(new_password) < 4: st.error("Password must be at least 4 characters long.")
            elif new_password != confirm_password: st.error("Passwords do not match. Try again!")
            else:
                user_index = roster_data.index[roster_data['Username'] == st.session_state['username']].tolist()[0]
                roster_data.at[user_index, 'Password'] = new_password
                roster_data.at[user_index, 'First_Login'] = "FALSE"
                
                push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                with st.spinner("Updating your account securely..."):
                    conn.update(worksheet="Roster", data=push_data)
                
                st.cache_data.clear()
                st.session_state["first_login"] = False
                st.rerun()

# --- HOME PAGE (DASHBOARD ROUTER) ---
def home_page():
    user_role = str(st.session_state["role"]).capitalize()
    
    st.title(f"{user_role}: {st.session_state['first_name']} {st.session_state['last_name']}")
    st.button("Log Out", on_click=logout)
    st.markdown("---")
    
    if user_role.upper() == "COACH":
        tab1, tab2, tab3 = st.tabs(["Athlete Lookup", "Roster Management", "Add Race Data"])
        
        with tab1:
            st.subheader("Athlete Lookup")
            active_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE") & 
                                          (roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"]))].copy()
            
            # Apply our Grade Math to the dropdown view
            active_athletes["Grade"] = active_athletes.get("Grad_Year", "Unknown").apply(get_grade_level)
            
            col_filter1, col_filter2 = st.columns(2)
            filter_gender = col_filter1.selectbox("Filter by Gender:", ["All", "Male", "Female"])
            filter_grade = col_filter2.selectbox("Filter by Grade:", ["All", "9th", "10th", "11th", "12th", "Middle School"])
            
            # Apply filters
            if filter_gender != "All":
                active_athletes = active_athletes[active_athletes["Gender"].str.title() == filter_gender]
            if filter_grade != "All":
                active_athletes = active_athletes[active_athletes["Grade"] == filter_grade]
                
            athlete_dict = {row["Username"]: f"{row['First_Name']} {row['Last_Name']} ({row['Grade']})" for _, row in active_athletes.iterrows()}
            
            if not athlete_dict:
                st.info("No active athletes match this filter.")
            else:
                selected_username = st.selectbox("Select an Athlete:", options=list(athlete_dict.keys()), format_func=lambda x: athlete_dict[x])
                if selected_username:
                    st.markdown(f"**Viewing data for: {athlete_dict[selected_username]}**")
                    display_athlete_races(selected_username)
                
        with tab2:
            st.subheader("Roster Management")
            roster_action = st.radio("Choose an action:", ["View Current Roster", "Add New Member", "Archive/Remove Member"], horizontal=True)
            st.markdown("---")
            
            if roster_action == "View Current Roster":
                active_roster = roster_data[roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"])].copy()
                if "Grad_Year" in active_roster.columns:
                    active_roster["Grade"] = active_roster["Grad_Year"].apply(get_grade_level)
                    display_roster = active_roster[["First_Name", "Last_Name", "Gender", "Grade", "Grad_Year", "Role"]].copy()
                    
                    # Sort primarily by Grad_Year (youngest to oldest or vice versa), then Gender, then Last Name
                    display_roster["Sort_Year"] = pd.to_numeric(display_roster["Grad_Year"], errors="coerce").fillna(9999)
                    display_roster = display_roster.sort_values(by=["Role", "Sort_Year", "Gender", "Last_Name"])
                    display_roster = display_roster.drop(columns=["Sort_Year"])
                    
                    st.dataframe(display_roster, hide_index=True, use_container_width=True)
                else:
                    st.dataframe(active_roster[["First_Name", "Last_Name", "Role"]].sort_values(by=["Last_Name"]), hide_index=True)

            elif roster_action == "Add New Member":
                with st.form("add_member_form"):
                    # Row 1: Names
                    r1_col1, r1_col2 = st.columns(2)
                    with r1_col1: new_first = st.text_input("First Name")
                    with r1_col2: new_last = st.text_input("Last Name")
                    
                    # Row 2: Role & Grad Year (Swapped locations!)
                    r2_col1, r2_col2 = st.columns(2)
                    with r2_col1: new_role = st.selectbox("Role", ["Athlete", "Coach"])
                    with r2_col2: new_grad_year = st.text_input("Grad Year (e.g., 2028)")
                    
                    # Row 3: Gender
                    r3_col1, r3_col2 = st.columns(2)
                    with r3_col1: new_gender = st.selectbox("Gender", ["Male", "Female", "N/A"])
                    
                    submit_new = st.form_submit_button("Add to Roster")
                    
                    if submit_new:
                        if not new_first or not new_last:
                            st.error("First and Last name are required.")
                        else:
                            # Backend Override & Validation
                            if new_role == "Coach":
                                final_grad_year = "Coach"
                                final_gender = "N/A"
                            else:
                                final_grad_year = new_grad_year.strip()
                                final_gender = new_gender
                                if not final_grad_year.isdigit() or len(final_grad_year) != 4:
                                    st.error("Please enter a valid 4-digit Graduation Year (e.g., 2028).")
                                    st.stop() # Stops the code from pushing bad data

                            generated_username = f"{new_first.lower()}.{new_last.lower()}".replace(" ", "")
                            new_row = pd.DataFrame([{
                                "Username": generated_username, "Password": "changeme",
                                "First_Name": new_first, "Last_Name": new_last,
                                "Role": new_role, "First_Login": "TRUE", "Active": "TRUE",
                                "Grad_Year": final_grad_year, "Gender": final_gender
                            }])
                            
                            push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                            updated_roster = pd.concat([push_data, new_row], ignore_index=True)
                            
                            with st.spinner("Adding new member..."):
                                conn.update(worksheet="Roster", data=updated_roster)
                            
                            st.success(f"Added {new_first} {new_last}! Username: '{generated_username}'. Password: 'changeme'.")
                            st.cache_data.clear()
                            st.rerun()

            elif roster_action == "Archive/Remove Member":
                st.warning("Archiving a runner hides them from the active roster.")
                active_athletes = roster_data[roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"])]
                archive_dict = {row["Username"]: f"{row['First_Name']} {row['Last_Name']}" for _, row in active_athletes.iterrows()}
                
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

    else:
        st.header("Race Results & Analytics")
        display_athlete_races(st.session_state["username"])

if not st.session_state["logged_in"]: login_page()
elif st.session_state["first_login"]: password_reset_page()
else: home_page()
