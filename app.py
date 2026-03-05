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

if "Active" in roster_data.columns:
    roster_data["Active_Clean"] = roster_data["Active"].astype(str).str.strip().str.upper()
else:
    roster_data["Active_Clean"] = "TRUE"
    
if "Gender" not in roster_data.columns:
    roster_data["Gender"] = "N/A"

expected_race_cols = ["Date", "Meet_Name", "Race_Name", "Distance", "Username", "Mile_1", "Mile_2", "Total_Time"]
for col in expected_race_cols:
    if col not in races_data.columns:
        races_data[col] = ""

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["first_name"] = ""
    st.session_state["last_name"] = ""
    st.session_state["role"] = ""
    st.session_state["first_login"] = False

for key in ["current_meet", "current_meet_date", "current_race", "current_distance"]:
    if key not in st.session_state:
        st.session_state[key] = None

def logout():
    for key in ["logged_in", "username", "first_name", "last_name", "role", "first_login"]:
        st.session_state[key] = False if key in ["logged_in", "first_login"] else ""
    for key in ["current_meet", "current_meet_date", "current_race", "current_distance"]:
        st.session_state[key] = None

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
        
        user_races["Date"] = pd.to_datetime(user_races["Date"], errors='coerce').dt.strftime('%m/%d/%Y').fillna("Unknown")
        
        unique_distances = user_races["Distance"].unique()
        
        for dist in unique_distances:
            st.subheader(f"{dist} Races")
            dist_races = user_races[user_races["Distance"] == dist].copy()
            
            display_cols = ["Date", "Meet_Name", "Race_Name", "Mile_1"]
            if str(dist).upper() == "5K": display_cols.append("Mile_2")
            display_cols.extend(["Final_Kick", "Total_Time", "Avg_Pace"])
            
            rename_dict = {"Meet_Name": "Meet", "Race_Name": "Race", "Mile_1": "Mile 1", "Mile_2": "Mile 2", 
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
                user_idx = roster_data.index[roster_data['Username'] == st.session_state['username']].tolist()[0]
                roster_data.at[user_idx, 'Password'] = new_password
                roster_data.at[user_idx, 'First_Login'] = "FALSE"
                
                push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                with st.spinner("Updating your account securely..."):
                    conn.update(worksheet="Roster", data=push_data)
                
                st.cache_data.clear()
                st.session_state["first_login"] = False
                st.rerun()

# --- HOME PAGE (DASHBOARD ROUTER) ---
def home_page():
    user_role = str(st.session_state["role"]).capitalize()
    
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1: st.title(f"{user_role}: {st.session_state['first_name']} {st.session_state['last_name']}")
    with col_header2: st.button("Log Out", on_click=logout, use_container_width=True)
    st.markdown("---")
    
    if user_role.upper() == "COACH":
        tab1, tab2, tab3 = st.tabs(["Athlete Lookup", "Roster Management", "Data Entry Command Center"])
        
        with tab1:
            st.subheader("Athlete Lookup")
            active_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE") & 
                                          (roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"]))].copy()
            
            active_athletes["Grade"] = active_athletes.get("Grad_Year", "Unknown").apply(get_grade_level)
            
            col_filter1, col_filter2 = st.columns(2)
            filter_gender = col_filter1.selectbox("Filter by Gender:", ["All", "Male", "Female"])
            filter_grade = col_filter2.selectbox("Filter by Grade:", ["All", "9th", "10th", "11th", "12th", "Middle School"])
            
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
                    display_athlete_races(selected_username)
                
        with tab2:
            st.subheader("Roster Management")
            roster_action = st.radio("Choose an action:", 
                                     ["View Current Roster", "Add New Member", "Edit Member", "Archive / Restore"], 
                                     horizontal=True)
            st.markdown("---")
            
            if roster_action == "View Current Roster":
                active_roster = roster_data[roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"])].copy()
                if "Grad_Year" in active_roster.columns:
                    active_roster["Grade"] = active_roster["Grad_Year"].apply(get_grade_level)
                    display_roster = active_roster[["First_Name", "Last_Name", "Gender", "Grade", "Grad_Year", "Role"]].copy()
                    display_roster["Sort_Year"] = pd.to_numeric(display_roster["Grad_Year"], errors="coerce").fillna(9999)
                    display_roster = display_roster.sort_values(by=["Role", "Sort_Year", "Gender", "Last_Name"])
                    display_roster = display_roster.drop(columns=["Sort_Year"])
                    st.dataframe(display_roster, hide_index=True, use_container_width=True)
                else:
                    st.dataframe(active_roster[["First_Name", "Last_Name", "Role"]].sort_values(by=["Last_Name"]), hide_index=True)

            elif roster_action == "Add New Member":
                with st.form("add_member_form"):
                    r1_col1, r1_col2 = st.columns(2)
                    with r1_col1: new_first = st.text_input("First Name")
                    with r1_col2: new_last = st.text_input("Last Name")
                    
                    r2_col1, r2_col2 = st.columns(2)
                    with r2_col1: new_role = st.selectbox("Role", ["Athlete", "Coach"])
                    with r2_col2: new_grad_year = st.text_input("Grad Year (e.g., 2028)")
                    
                    r3_col1, r3_col2 = st.columns(2)
                    with r3_col1: new_gender = st.selectbox("Gender", ["Male", "Female", "N/A"])
                    
                    if st.form_submit_button("Add to Roster"):
                        if not new_first or not new_last: st.error("First and Last name are required.")
                        else:
                            if new_role == "Coach": final_grad_year, final_gender = "Coach", "N/A"
                            else:
                                final_grad_year, final_gender = new_grad_year.strip(), new_gender
                                if not final_grad_year.isdigit() or len(final_grad_year) != 4:
                                    st.error("❌ Data Error: Graduation Year must be a 4-digit number.")
                                    st.stop() 

                            base_username = f"{new_first.lower()}.{new_last.lower()}".replace(" ", "")
                            generated_username = base_username
                            existing_usernames = roster_data["Username"].tolist()
                            suffix = 1
                            while generated_username in existing_usernames:
                                generated_username = f"{base_username}{suffix}"
                                suffix += 1

                            new_row = pd.DataFrame([{"Username": generated_username, "Password": "changeme", "First_Name": new_first, "Last_Name": new_last, "Role": new_role, "First_Login": "TRUE", "Active": "TRUE", "Grad_Year": final_grad_year, "Gender": final_gender}])
                            push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                            updated_roster = pd.concat([push_data, new_row], ignore_index=True)
                            with st.spinner("Adding new member..."): conn.update(worksheet="Roster", data=updated_roster)
                            st.success(f"Added {new_first} {new_last}! Username: '{generated_username}'.")
                            st.cache_data.clear()
                            st.rerun()

            elif roster_action == "Edit Member":
                st.info("💡 Note: You cannot edit Usernames.")
                active_athletes = roster_data[roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"])]
                edit_dict = {row["Username"]: f"{row['First_Name']} {row['Last_Name']} ({row.get('Role', '')})" for _, row in active_athletes.iterrows()}
                
                if not edit_dict: st.info("No active members to edit.")
                else:
                    user_to_edit = st.selectbox("Select Member to Edit:", options=list(edit_dict.keys()), format_func=lambda x: edit_dict[x])
                    if user_to_edit:
                        target_row = roster_data[roster_data["Username"] == user_to_edit].iloc[0]
                        with st.form("edit_member_form"):
                            e1_col1, e1_col2 = st.columns(2)
                            with e1_col1: edit_first = st.text_input("First Name", value=target_row["First_Name"])
                            with e1_col2: edit_last = st.text_input("Last Name", value=target_row["Last_Name"])
                            e2_col1, e2_col2 = st.columns(2)
                            with e2_col1:
                                role_index = 0 if str(target_row["Role"]).title() == "Athlete" else 1
                                edit_role = st.selectbox("Role", ["Athlete", "Coach"], index=role_index)
                            with e2_col2: edit_grad_year = st.text_input("Grad Year", value=str(target_row.get("Grad_Year", "")))
                            e3_col1, e3_col2 = st.columns(2)
                            with e3_col1:
                                gender_val = str(target_row.get("Gender", "N/A")).title()
                                gender_opts = ["Male", "Female", "N/A"]
                                g_index = gender_opts.index(gender_val) if gender_val in gender_opts else 2
                                edit_gender = st.selectbox("Gender", gender_opts, index=g_index)
                                
                            if st.form_submit_button("Save Changes"):
                                if edit_role != "Coach":
                                    if not edit_grad_year.strip().isdigit() or len(edit_grad_year.strip()) != 4:
                                        st.error("❌ Data Error: Graduation Year must be a 4-digit number.")
                                        st.stop()
                                user_idx = roster_data.index[roster_data['Username'] == user_to_edit].tolist()[0]
                                roster_data.at[user_idx, 'First_Name'] = edit_first
                                roster_data.at[user_idx, 'Last_Name'] = edit_last
                                roster_data.at[user_idx, 'Role'] = edit_role
                                roster_data.at[user_idx, 'Grad_Year'] = "Coach" if edit_role == "Coach" else edit_grad_year.strip()
                                roster_data.at[user_idx, 'Gender'] = "N/A" if edit_role == "Coach" else edit_gender
                                push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                                with st.spinner("Saving changes..."): conn.update(worksheet="Roster", data=push_data)
                                st.success("Member updated successfully!")
                                st.cache_data.clear()
                                st.rerun()

            elif roster_action == "Archive / Restore":
                arc_tab1, arc_tab2, arc_tab3 = st.tabs(["Archive Individual", "Restore Member", "🎓 Graduate Seniors"])
                with arc_tab1:
                    active_athletes = roster_data[roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"])]
                    archive_dict = {row["Username"]: f"{row['First_Name']} {row['Last_Name']}" for _, row in active_athletes.iterrows()}
                    if not archive_dict: st.info("No active members to archive.")
                    else:
                        user_to_archive = st.selectbox("Select Member to Archive:", options=list(archive_dict.keys()), format_func=lambda x: archive_dict[x])
                        if st.button("Archive Member"):
                            user_idx = roster_data.index[roster_data['Username'] == user_to_archive].tolist()[0]
                            roster_data.at[user_idx, 'Active'] = "FALSE"
                            push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                            conn.update(worksheet="Roster", data=push_data)
                            st.cache_data.clear()
                            st.rerun()
                with arc_tab2:
                    inactive_athletes = roster_data[~roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"])]
                    restore_dict = {row["Username"]: f"{row['First_Name']} {row['Last_Name']}" for _, row in inactive_athletes.iterrows()}
                    if not restore_dict: st.info("There are no archived members to restore.")
                    else:
                        user_to_restore = st.selectbox("Select Member to Restore:", options=list(restore_dict.keys()), format_func=lambda x: restore_dict[x])
                        if st.button("Restore Member"):
                            user_idx = roster_data.index[roster_data['Username'] == user_to_restore].tolist()[0]
                            roster_data.at[user_idx, 'Active'] = "TRUE"
                            push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                            conn.update(worksheet="Roster", data=push_data)
                            st.cache_data.clear()
                            st.rerun()
                with arc_tab3:
                    st.warning("This will archive all active runners whose Grade Level is calculated as '12th'.")
                    active_df = roster_data[roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"])].copy()
                    active_df["Grade"] = active_df.get("Grad_Year", "Unknown").apply(get_grade_level)
                    seniors = active_df[active_df["Grade"] == "12th"]
                    if seniors.empty: st.info("No active seniors found.")
                    else:
                        for _, senior in seniors.iterrows(): st.markdown(f"- {senior['First_Name']} {senior['Last_Name']}")
                        if st.button("Confirm: Archive All Seniors"):
                            for _, senior in seniors.iterrows():
                                s_idx = roster_data.index[roster_data['Username'] == senior['Username']].tolist()[0]
                                roster_data.at[s_idx, 'Active'] = "FALSE"
                            push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                            with st.spinner("Archiving seniors..."): conn.update(worksheet="Roster", data=push_data)
                            st.cache_data.clear()
                            st.rerun()

        with tab3:
            st.subheader("Race Data Entry")
            
            # --- TOP BAR: RESET BUTTON ---
            if st.session_state.current_meet:
                reset_col1, reset_col2 = st.columns([3, 1])
                with reset_col1:
                    st.success(f"📍 **Meet Locked:** {st.session_state.current_meet} ({st.session_state.current_meet_date})")
                with reset_col2:
                    if st.button("🔄 Change Meet"):
                        st.session_state.current_meet = None
                        st.session_state.current_race = None
                        st.rerun()
            
            # --- STEP 1: SET MEET ---
            if not st.session_state.current_meet:
                st.markdown("### Step 1: Select or Create a Meet")
                existing_meets = races_data[races_data["Meet_Name"].astype(str).str.strip() != ""]["Meet_Name"].dropna().unique().tolist()
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown("**Use Existing Meet**")
                    if existing_meets:
                        sel_meet = st.selectbox("Choose Meet", existing_meets)
                        if st.button("Set Existing Meet"):
                            m_date_val = races_data[races_data["Meet_Name"] == sel_meet]["Date"].dropna().iloc[0]
                            st.session_state.current_meet = sel_meet
                            st.session_state.current_meet_date = pd.to_datetime(m_date_val, errors='coerce').date()
                            st.rerun()
                    else:
                        st.info("No existing meets found.")
                        
                with col_m2:
                    st.markdown("**Create New Meet**")
                    new_meet = st.text_input("New Meet Name")
                    new_date = st.date_input("Meet Date")
                    if st.button("Create New Meet"):
                        if new_meet:
                            st.session_state.current_meet = new_meet
                            st.session_state.current_meet_date = new_date
                            st.rerun()
                        else:
                            st.error("Please enter a Meet Name.")

            # --- STEP 2: SET RACE ---
            elif st.session_state.current_meet and not st.session_state.current_race:
                st.markdown("### Step 2: Select or Create a Race")
                
                meet_races_df = races_data[races_data["Meet_Name"] == st.session_state.current_meet]
                existing_races = meet_races_df[meet_races_df["Race_Name"].astype(str).str.strip() != ""]["Race_Name"].dropna().unique().tolist()
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.markdown("**Use Existing Race**")
                    if existing_races:
                        sel_race = st.selectbox("Choose Race", existing_races)
                        if st.button("Set Existing Race"):
                            r_dist = meet_races_df[meet_races_df["Race_Name"] == sel_race]["Distance"].dropna().iloc[0]
                            st.session_state.current_race = sel_race
                            st.session_state.current_distance = r_dist
                            st.rerun()
                    else:
                        st.info("No races saved for this meet yet.")
                        
                with col_r2:
                    st.markdown("**Create New Race**")
                    new_race = st.text_input("New Race Category (e.g., Boys JV)")
                    new_dist = st.selectbox("Distance", ["5K", "2 Mile", "Other"])
                    if st.button("Create New Race"):
                        if new_race:
                            st.session_state.current_race = new_race
                            st.session_state.current_distance = new_dist
                            st.rerun()
                        else:
                            st.error("Please enter a Race Category.")

            # --- STEP 3: LOG TIMES ---
            elif st.session_state.current_meet and st.session_state.current_race:
                
                col_info1, col_info2 = st.columns([3, 1])
                with col_info1:
                    st.info(f"🏁 **Race Locked:** {st.session_state.current_race} ({st.session_state.current_distance})")
                with col_info2:
                    if st.button("🔄 Change Race"):
                        st.session_state.current_race = None
                        st.rerun()

                st.markdown("---")
                st.subheader("🏃 Log Runner Times")
                
                active_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE") & 
                                              (roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"]))].copy()
                active_athletes = active_athletes.sort_values(by=["Gender", "Last_Name"])
                runner_dict = {row["Username"]: f"{row['First_Name']} {row['Last_Name']} ({row.get('Gender', 'N/A')})" for _, row in active_athletes.iterrows()}
                
                with st.form("add_race_result_form", clear_on_submit=True):
                    runner_selected = st.selectbox("Select Runner:", options=list(runner_dict.keys()), format_func=lambda x: runner_dict[x])
                    
                    time_col1, time_col2, time_col3 = st.columns(3)
                    with time_col1: m1_time = st.text_input("Mile 1 Split", placeholder="e.g., 5:30")
                    with time_col2:
                        if st.session_state.current_distance == "5K":
                            m2_time = st.text_input("Mile 2 Split", placeholder="e.g., 11:15")
                        else:
                            m2_time = ""
                            st.caption("Mile 2 hidden for 2-mile race.")
                    with time_col3: total_time = st.text_input("Total Finish Time", placeholder="e.g., 17:45")
                        
                    if st.form_submit_button("Save Result & Next"):
                        if not total_time:
                            st.error("Total Finish Time is required.")
                        else:
                            formatted_date = pd.to_datetime(st.session_state.current_meet_date).strftime("%Y-%m-%d")
                            new_race_row = pd.DataFrame([{
                                "Date": formatted_date,
                                "Meet_Name": st.session_state.current_meet,
                                "Race_Name": st.session_state.current_race,
                                "Distance": st.session_state.current_distance,
                                "Username": runner_selected,
                                "Mile_1": m1_time,
                                "Mile_2": m2_time,
                                "Total_Time": total_time
                            }])
                            
                            updated_races = pd.concat([races_data, new_race_row], ignore_index=True)
                            with st.spinner(f"Saving time for {runner_dict[runner_selected]}..."):
                                conn.update(worksheet="Races", data=updated_races)
                            
                            st.success(f"Saved {total_time} for {runner_dict[runner_selected]}!")
                            st.cache_data.clear()
                            st.rerun()
                
                # --- MINI VIEW: SHOW RECENT ENTRIES ---
                st.markdown("#### Previously Entered for this Race")
                recent_entries = races_data[(races_data["Meet_Name"] == st.session_state.current_meet) & 
                                            (races_data["Race_Name"] == st.session_state.current_race)].copy()
                
                if not recent_entries.empty:
                    athlete_lookup = {row["Username"]: f"{row['First_Name']} {row['Last_Name']}" for _, row in roster_data.iterrows()}
                    recent_entries["Athlete"] = recent_entries["Username"].map(athlete_lookup)
                    display_cols = ["Athlete", "Mile_1", "Mile_2", "Total_Time"] if st.session_state.current_distance == "5K" else ["Athlete", "Mile_1", "Total_Time"]
                    st.dataframe(recent_entries[display_cols], hide_index=True, use_container_width=True)
                
                # --- NEW "DONE" BUTTONS SECTION ---
                st.markdown("---")
                st.markdown("#### Finished Logging?")
                done_col1, done_col2 = st.columns(2)
                with done_col1:
                    if st.button("🏁 Done with this Race", use_container_width=True):
                        st.session_state.current_race = None
                        st.rerun()
                with done_col2:
                    if st.button("🏠 Done with this Meet", use_container_width=True):
                        st.session_state.current_meet = None
                        st.session_state.current_race = None
                        st.rerun()

    else:
        st.header("Race Results & Analytics")
        display_athlete_races(st.session_state["username"])

if not st.session_state["logged_in"]: login_page()
elif st.session_state["first_login"]: password_reset_page()
else: home_page()
