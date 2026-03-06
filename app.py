import streamlit as st
import pandas as pd
import datetime
import plotly.express as px  # For interactive charting
from streamlit_gsheets import GSheetsConnection

# ==========================================
# --- 1. APP SETUP & VISUAL THEMES ---
# ==========================================
st.set_page_config(page_title="MCXC Team Dashboard", layout="centered", page_icon="🏃")

# Define expanded visual themes (Now with backgrounds, text colors, and chart templates!)
THEMES = {
    "MCXC Classic (Light)": {
        "bar": "linear-gradient(to right, #8B2331, #0C223F, #C7B683)", 
        "metric_bg": "rgba(139, 35, 49, 0.05)", "metric_border": "rgba(139, 35, 49, 0.2)",
        "line": "#8B2331", "app_bg": "#FFFFFF", "text": "#31333F", 
        "sidebar_bg": "#F0F2F6", "plotly_template": "plotly_white"
    },
    "Midnight Runner (Dark)": {
        "bar": "linear-gradient(to right, #FF4B4B, #FF904F)", 
        "metric_bg": "rgba(255, 75, 75, 0.1)", "metric_border": "rgba(255, 75, 75, 0.3)",
        "line": "#FF4B4B", "app_bg": "#0E1117", "text": "#FAFAFA", 
        "sidebar_bg": "#262730", "plotly_template": "plotly_dark"
    },
    "Neon Track (Dark)": {
        "bar": "linear-gradient(to right, #FF007F, #7928CA, #00C9FF)", 
        "metric_bg": "rgba(121, 40, 202, 0.15)", "metric_border": "rgba(255, 0, 127, 0.4)",
        "line": "#FF007F", "app_bg": "#121212", "text": "#E0E0E0", 
        "sidebar_bg": "#1E1E1E", "plotly_template": "plotly_dark"
    },
    "Ocean Pace (Light)": {
        "bar": "linear-gradient(to right, #00C9FF, #92FE9D)", 
        "metric_bg": "rgba(0, 201, 255, 0.05)", "metric_border": "rgba(0, 201, 255, 0.3)",
        "line": "#00C9FF", "app_bg": "#F4F8FB", "text": "#1A2A3A", 
        "sidebar_bg": "#E5F0F9", "plotly_template": "plotly_white"
    }
}

# Ensure a theme is always selected in session state
if "theme" not in st.session_state:
    st.session_state["theme"] = "MCXC Classic (Light)"

current_theme = THEMES[st.session_state["theme"]]

# Inject heavy-duty CSS to override Streamlit's default backgrounds and text
st.markdown(f"""
    <style>
        /* Main App Background */
        .stApp {{
            background-color: {current_theme['app_bg']};
        }}
        /* Sidebar Background */
        [data-testid="stSidebar"] {{
            background-color: {current_theme['sidebar_bg']};
        }}
        /* Force Header to be transparent so background shows through */
        [data-testid="stHeader"] {{
            background-color: transparent;
        }}
        /* Top Gradient Bar */
        .color-bar {{
            height: 8px;
            background: {current_theme['bar']};
            margin-bottom: 2rem;
            border-radius: 4px;
        }}
        /* Metric Containers */
        div[data-testid="metric-container"] {{
            background-color: {current_theme['metric_bg']};
            border: 1px solid {current_theme['metric_border']};
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        /* Override primary text colors (Headings, Paragraphs, Labels) */
        h1, h2, h3, h4, p, span, label {{
            color: {current_theme['text']} !important;
        }}
    </style>
    <div class="color-bar"></div>
""", unsafe_allow_html=True)


# ==========================================
# --- 2. MATH & LOGIC FUNCTIONS ---
# ==========================================
def time_to_seconds(time_str):
    if pd.isna(time_str) or time_str == "" or str(time_str).strip() == "": return 0
    time_str = str(time_str).strip()
    if ":" in time_str:
        parts = time_str.split(':')
        return int(parts[0]) * 60 + float(parts[1])
    return 0

def seconds_to_time(seconds):
    if seconds <= 0: return ""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"

def parse_fast_time(val, mode):
    # Handles numbers typed without colons (e.g., 530 instead of 5:30)
    if pd.isna(val) or str(val).strip() == "": return ""
    val_str = str(val).strip()
    if ":" in val_str: return val_str
    if not val_str.isdigit(): return val_str 
    
    num = int(val_str)
    if "Total Seconds" in mode:
        mins = num // 60
        secs = num % 60
        return f"{mins}:{secs:02d}"
    else:
        if len(val_str) <= 2:
            mins = num // 60
            secs = num % 60
            return f"{mins}:{secs:02d}"
        else:
            secs = int(val_str[-2:])
            mins = int(val_str[:-2])
            mins += secs // 60
            secs = secs % 60
            return f"{mins}:{secs:02d}"

def get_grade_level(grad_year_str):
    if str(grad_year_str).upper() == "COACH" or not str(grad_year_str).strip().isdigit(): return "Coach"
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

# ==========================================
# --- 3. DATABASE CONNECTION & CLEANUP ---
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the tabs from Google Sheets and instantly drop empty rows
roster_data = conn.read(worksheet="Roster", ttl=600).dropna(how="all")
races_data = conn.read(worksheet="Races", ttl=600).dropna(how="all")
workouts_data = conn.read(worksheet="Workouts", ttl=600).dropna(how="all")

# CRITICAL BUG FIX: Strip "Ghost Rows"
# Removes blank rows that Google Sheets generates by default so they don't crash the app
if "Username" in roster_data.columns:
    roster_data = roster_data[roster_data["Username"].astype(str).str.strip() != ""]
    roster_data = roster_data.dropna(subset=["Username"])

if "Username" in races_data.columns:
    races_data = races_data[races_data["Username"].astype(str).str.strip() != ""]
    races_data = races_data.dropna(subset=["Username"])

if "Username" in workouts_data.columns:
    workouts_data = workouts_data[workouts_data["Username"].astype(str).str.strip() != ""]
    workouts_data = workouts_data.dropna(subset=["Username"])

# Clean up basic Roster data to prevent errors
if "Active" in roster_data.columns: 
    roster_data["Active_Clean"] = roster_data["Active"].astype(str).str.strip().str.upper()
else: 
    roster_data["Active_Clean"] = "TRUE"
    
if "Gender" not in roster_data.columns: 
    roster_data["Gender"] = "N/A"

# Ensure all expected columns exist in Races
expected_race_cols = ["Date", "Meet_Name", "Race_Name", "Distance", "Username", "Mile_1", "Mile_2", "Total_Time", "Weight"]
for col in expected_race_cols:
    if col not in races_data.columns: 
        races_data[col] = 1.0 if col == "Weight" else ""
races_data["Weight"] = pd.to_numeric(races_data["Weight"], errors="coerce").fillna(1.0)

# Ensure all expected columns exist in Workouts
expected_workout_cols = ["Date", "Workout_Type", "Rep_Distance", "Weather", "Username", "Status", "Splits"]
for col in expected_workout_cols:
    if col not in workouts_data.columns: 
        workouts_data[col] = ""

# ==========================================
# --- 4. SESSION STATE MANAGEMENT ---
# ==========================================
# Keep track of who is logged in and what they are doing
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    for key in ["username", "first_name", "last_name", "role"]: st.session_state[key] = ""
    st.session_state["first_login"] = False

for key in ["current_meet", "current_meet_date", "current_race", "current_distance"]:
    if key not in st.session_state: st.session_state[key] = None

if "workout_saved" not in st.session_state: st.session_state["workout_saved"] = False

def logout():
    for key in ["logged_in", "first_login", "workout_saved"]: st.session_state[key] = False
    for key in ["username", "first_name", "last_name", "role"]: st.session_state[key] = ""
    for key in ["current_meet", "current_meet_date", "current_race", "current_distance"]: st.session_state[key] = None


# ==========================================
# --- 5. VISUAL UI COMPONENTS & CHARTS ---
# ==========================================
def show_rankings_tab():
    st.subheader("Team Rankings & Season Grid")
    
    # Filters for Gender and Distance
    r_col1, r_col2 = st.columns(2)
    with r_col1: r_gender = st.selectbox("Category", ["Men's", "Women's"], key="rankings_category")
    with r_col2: r_dist = st.selectbox("Distance", ["5K", "2 Mile"], key="rankings_distance")
        
    target_gender = "Male" if r_gender == "Men's" else "Female"
    
    # Merge Races and Roster
    merged = pd.merge(races_data, roster_data[["Username", "First_Name", "Last_Name", "Gender", "Active_Clean"]], on="Username", how="inner")
    merged = merged[merged["Active_Clean"].isin(["TRUE", "1", "1.0"])]
    merged = merged[(merged["Gender"].str.title() == target_gender) & (merged["Distance"].str.upper() == r_dist.upper())]
    
    if merged.empty:
        st.info("No race data found for this category.")
        return
    
    # Sub-Tabs for different viewing modes
    tab_lead, tab_grid = st.tabs(["🏆 Leaderboard", "📅 Master Grid"])
    
    with tab_lead:
        r_metric = st.radio("Rank By:", ["Weighted Average", "Personal Record (PR)"], horizontal=True, key="rankings_metric")
        
        merged["Time_Sec"] = merged["Total_Time"].apply(time_to_seconds)
        merged["Weight"] = pd.to_numeric(merged["Weight"], errors="coerce").fillna(1.0)
        
        results = []
        for user, group in merged.groupby("Username"):
            valid_races = group[group["Weight"] > 0] # Filter out explicitly ignored races
            if valid_races.empty: continue
                
            if r_metric == "Personal Record (PR)":
                best_time = valid_races["Time_Sec"].min()
                results.append({"Athlete": f"{group.iloc[0]['First_Name']} {group.iloc[0]['Last_Name']}", "Time_Sec": best_time, "Mark": seconds_to_time(best_time)})
            else: # Weighted Average
                total_weight = valid_races["Weight"].sum()
                if total_weight <= 0: continue
                weighted_sum = (valid_races["Time_Sec"] * valid_races["Weight"]).sum()
                avg_time = weighted_sum / total_weight
                results.append({"Athlete": f"{group.iloc[0]['First_Name']} {group.iloc[0]['Last_Name']}", "Time_Sec": avg_time, "Mark": seconds_to_time(avg_time)})
                
        if not results:
            st.info("No valid ranked data (check if races have a weight of 0).")
        else:
            rank_df = pd.DataFrame(results).sort_values(by="Time_Sec").reset_index(drop=True)
            rank_df.index = rank_df.index + 1
            rank_df = rank_df.rename_axis("Rank").reset_index()
            
            display_df = rank_df[["Rank", "Athlete", "Mark"]]
            display_df = display_df.rename(columns={"Mark": "PR Time" if r_metric == "Personal Record (PR)" else "Weighted Avg Time"})
            st.dataframe(display_df, hide_index=True, use_container_width=True)

    with tab_grid:
        st.markdown(f"### Master {r_dist} Grid")
        st.caption("Chronological view of all race performances.")
        
        grid_df = merged.copy()
        grid_df["Athlete"] = grid_df["First_Name"] + " " + grid_df["Last_Name"]
        
        # Sort chronologically so columns appear in the order the races happened
        grid_df["Date_Obj"] = pd.to_datetime(grid_df["Date"], errors='coerce')
        grid_df = grid_df.sort_values(by="Date_Obj")
        
        # Create a clean column name like "State Champs (10/15)"
        grid_df["Race_Col"] = grid_df["Meet_Name"] + " (" + grid_df["Date_Obj"].dt.strftime('%m/%d').fillna("") + ")"
        
        # Capture the chronological order of the races
        ordered_cols = grid_df["Race_Col"].unique().tolist()
        
        # Pivot the table: Athletes as rows, Races as columns, Times as values
        pivot_df = grid_df.pivot_table(index="Athlete", columns="Race_Col", values="Total_Time", aggfunc="first")
        
        # Reorder columns chronologically, fill blank cells with a dash, and reset index to show Athlete column
        pivot_df = pivot_df.reindex(columns=ordered_cols).fillna("-").reset_index()
        
        st.dataframe(pivot_df, hide_index=True, use_container_width=True)True)

def plot_athlete_progress(user_races):
    # Filter only for 5K races with valid times
    df = user_races[(user_races["Distance"].str.upper() == "5K") & (user_races["Time_Sec"] > 0)].copy()
    if df.empty or len(df) < 2:
        return # Not enough data to draw a meaningful line chart
    
    # Prep data for Plotly
    df["Date_Obj"] = pd.to_datetime(df["Date"], errors='coerce')
    df = df.sort_values("Date_Obj")
    df["Time_Min"] = df["Time_Sec"] / 60.0  # Convert to minutes for the Y-axis scale
    
    # Create the interactive line chart
    fig = px.line(
        df, x="Date_Obj", y="Time_Min", markers=True, 
        title="📈 5K Progression",
        hover_data={"Date_Obj": "|%b %d, %Y", "Time_Min": False, "Total_Time": True, "Meet_Name": True}
    )
    
    # Reverse the Y-axis so FASTER times (lower numbers) are visually HIGHER on the chart
    fig.update_yaxes(title="Finish Time (Minutes)", autorange="reversed")
    fig.update_xaxes(title="Race Date")
    
    # NEW: Apply the selected theme's Plotly template (Dark/Light mode for the chart background)
    fig.update_layout(template=THEMES[st.session_state["theme"]]["plotly_template"])
    
    # Theme color formatting for the actual line
    theme_line_color = THEMES[st.session_state["theme"]]["line"]
    fig.update_traces(line_color=theme_line_color, line_width=3, marker_size=8)
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

def display_athlete_races(target_username):
    user_races = races_data[races_data["Username"] == target_username].copy()
    if not user_races.empty:
        user_races["Time_Sec"] = user_races["Total_Time"].apply(time_to_seconds)
        user_races = user_races[user_races["Time_Sec"] > 0] # Hide empty rows
        
        # Display the visual chart first!
        plot_athlete_progress(user_races)
        
        def calculate_avg_pace(row):
            distance_mi = 3.10686 if str(row["Distance"]).upper() == "5K" else 2.0
            return seconds_to_time(row["Time_Sec"] / distance_mi)
        def calculate_kick(row):
            m1_sec = time_to_seconds(row["Mile_1"])
            m2_sec = time_to_seconds(row["Mile_2"])
            return seconds_to_time(row["Time_Sec"] - (m1_sec + m2_sec))
            
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
            rename_dict = {"Meet_Name": "Meet", "Race_Name": "Race", "Mile_1": "Mile 1", "Mile_2": "Mile 2", "Final_Kick": "Final Kick", "Total_Time": "Total Time", "Avg_Pace": "Avg Pace"}
            clean_table = dist_races[display_cols].rename(columns=rename_dict)
            st.dataframe(clean_table, hide_index=True, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("No race data found yet for this season.")

def display_athlete_workouts(target_username):
    user_workouts = workouts_data[workouts_data["Username"] == target_username].copy()
    if not user_workouts.empty:
        user_workouts["Date_Obj"] = pd.to_datetime(user_workouts["Date"], errors='coerce')
        user_workouts = user_workouts.sort_values(by="Date_Obj", ascending=False)
        user_workouts["Date"] = user_workouts["Date_Obj"].dt.strftime('%m/%d/%Y').fillna("Unknown")
        
        display_cols = ["Date", "Workout_Type", "Rep_Distance", "Status", "Splits", "Weather"]
        rename_dict = {"Workout_Type": "Type", "Rep_Distance": "Details"}
        clean_table = user_workouts[display_cols].rename(columns=rename_dict)
        st.dataframe(clean_table, hide_index=True, use_container_width=True)
    else:
        st.info("No workout data found yet for this season.")


# ==========================================
# --- 6. LOGIN & SECURITY PAGES ---
# ==========================================
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
                if not is_active: st.error("This account is no longer active.")
                elif password == str(user_row.iloc[0]["Password"]):
                    st.session_state.update({"logged_in": True, "username": username, "first_name": user_row.iloc[0]["First_Name"], "last_name": user_row.iloc[0]["Last_Name"], "role": user_row.iloc[0]["Role"]})
                    st.session_state["first_login"] = str(user_row.iloc[0]["First_Login"]).strip().upper() in ["TRUE", "1", "1.0"]
                    st.rerun()
                else: st.error("Incorrect password.")
            else: st.error("Username not found.")

def password_reset_page():
    st.title("Welcome to the Team")
    st.markdown("Please create a new, secure password to continue.")
    with st.form("reset_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password"):
            if len(new_password) < 4: st.error("Password must be at least 4 characters long.")
            elif new_password != confirm_password: st.error("Passwords do not match.")
            else:
                user_idx = roster_data.index[roster_data['Username'] == st.session_state['username']].tolist()[0]
                roster_data.at[user_idx, 'Password'] = new_password
                roster_data.at[user_idx, 'First_Login'] = "FALSE"
                push_data = roster_data.drop(columns=["Active_Clean"]) if "Active_Clean" in roster_data.columns else roster_data
                with st.spinner("Updating account..."): conn.update(worksheet="Roster", data=push_data)
                st.cache_data.clear()
                st.session_state["first_login"] = False
                st.rerun()


# ==========================================
# --- 7. HOME PAGE ROUTER (DASHBOARD) ---
# ==========================================
def home_page():
    user_role = str(st.session_state["role"]).capitalize()
    
    # SIDEBAR logic for Themes & Settings
    with st.sidebar:
        st.subheader("⚙️ Settings")
        selected_theme = st.selectbox("App Theme", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state["theme"]))
        if selected_theme != st.session_state["theme"]:
            st.session_state["theme"] = selected_theme
            st.rerun()
        st.markdown("---")
        st.button("Log Out", on_click=logout, use_container_width=True)
    
    # Main Header
    st.title(f"{user_role}: {st.session_state['first_name']} {st.session_state['last_name']}")
    st.markdown("---")
    
    # ----------------------------------
    # COACH VIEW
    # ----------------------------------
    if user_role.upper() == "COACH":
        tab1, tab2, tab3, tab4 = st.tabs(["Athlete Lookup", "Roster Management", "Data Entry", "Team Rankings"])
        
        with tab1:
            st.subheader("Athlete Lookup")
            active_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE") & (roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"]))].copy()
            active_athletes["Grade"] = active_athletes.get("Grad_Year", "Unknown").apply(get_grade_level)
            col_filter1, col_filter2 = st.columns(2)
            filter_gender = col_filter1.selectbox("Filter by Gender:", ["All", "Male", "Female"])
            filter_grade = col_filter2.selectbox("Filter by Grade:", ["All", "9th", "10th", "11th", "12th", "Middle School"])
            if filter_gender != "All": active_athletes = active_athletes[active_athletes["Gender"].str.title() == filter_gender]
            if filter_grade != "All": active_athletes = active_athletes[active_athletes["Grade"] == filter_grade]
            athlete_dict = {row["Username"]: f"{row['First_Name']} {row['Last_Name']} ({row['Grade']})" for _, row in active_athletes.iterrows()}
            if not athlete_dict: st.info("No active athletes match this filter.")
            else:
                selected_username = st.selectbox("Select an Athlete:", options=list(athlete_dict.keys()), format_func=lambda x: athlete_dict[x])
                if selected_username: 
                    st.markdown("---")
                    sub_tab1, sub_tab2 = st.tabs(["Race Results", "Workouts"])
                    with sub_tab1: display_athlete_races(selected_username)
                    with sub_tab2: display_athlete_workouts(selected_username)
                
        with tab2:
            st.subheader("Roster Management")
            roster_action = st.radio("Choose an action:", ["View Current Roster", "Add New Member", "Edit Member", "Archive / Restore"], horizontal=True)
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
                                    st.error("Data Error: Graduation Year must be a 4-digit number.")
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
                st.info("Note: You cannot edit Usernames.")
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
                                        st.error("Data Error: Graduation Year must be a 4-digit number.")
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
                arc_tab1, arc_tab2, arc_tab3 = st.tabs(["Archive Individual", "Restore Member", "Graduate Seniors"])
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
            de_type = st.radio("Select Entry Mode", ["Race Results", "Workouts", "Manage Race Weights"], horizontal=True)
            st.markdown("---")
            
            if de_type == "Manage Race Weights":
                st.subheader("Manage Race Multipliers & Weights")
                st.markdown("Adjust how heavily a race impacts the **Weighted Average** Rankings. Set a race to **0** to hide it from rankings entirely, or **2.0** to double its weight.")
                
                unique_races = races_data[["Meet_Name", "Race_Name", "Distance", "Date", "Weight"]].drop_duplicates(subset=["Meet_Name", "Race_Name", "Date"])
                if unique_races.empty or unique_races["Meet_Name"].isna().all(): st.info("No races logged yet.")
                else:
                    with st.form("weights_form"):
                        updated_weights = {}
                        # Bug Fix applied: Using index as unique key!
                        for index, row in unique_races.iterrows():
                            meet = row["Meet_Name"]
                            race = row["Race_Name"]
                            date = row["Date"]
                            current_w = row["Weight"]
                            label = f"{pd.to_datetime(date, errors='coerce').strftime('%m/%d/%Y')} | {meet} - {race} ({row['Distance']})"
                            
                            new_w = st.number_input(label, value=float(current_w), step=0.5, min_value=0.0, key=f"weight_input_{index}")
                            updated_weights[(meet, race, date)] = new_w
                            
                        if st.form_submit_button("Save Weights", type="primary"):
                            for (m, r, d), w in updated_weights.items():
                                mask = (races_data["Meet_Name"] == m) & (races_data["Race_Name"] == r) & (races_data["Date"] == d)
                                races_data.loc[mask, "Weight"] = w
                            with st.spinner("Updating database..."): conn.update(worksheet="Races", data=races_data)
                            st.success("Weights updated successfully!")
                            st.cache_data.clear()
                            st.rerun()

            elif de_type == "Race Results":
                st.subheader("Race Data Entry")
                if st.session_state.current_meet:
                    reset_col1, reset_col2 = st.columns([3, 1])
                    with reset_col1: st.success(f"Meet Locked: {st.session_state.current_meet} ({st.session_state.current_meet_date})")
                    with reset_col2:
                        if st.button("Change Meet"):
                            st.session_state.current_meet, st.session_state.current_race = None, None
                            st.rerun()
                
                if not st.session_state.current_meet:
                    st.markdown("### Step 1: Select or Create a Meet")
                    existing_meets = races_data[races_data["Meet_Name"].astype(str).str.strip() != ""]["Meet_Name"].dropna().unique().tolist()
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        if existing_meets:
                            sel_meet = st.selectbox("Choose Meet", existing_meets)
                            if st.button("Set Existing Meet"):
                                m_date_val = races_data[races_data["Meet_Name"] == sel_meet]["Date"].dropna().iloc[0]
                                st.session_state.current_meet = sel_meet
                                st.session_state.current_meet_date = pd.to_datetime(m_date_val, errors='coerce').date()
                                st.rerun()
                    with col_m2:
                        new_meet = st.text_input("New Meet Name")
                        new_date = st.date_input("Meet Date")
                        if st.button("Create New Meet"):
                            if new_meet:
                                st.session_state.current_meet, st.session_state.current_meet_date = new_meet, new_date
                                st.rerun()

                elif st.session_state.current_meet and not st.session_state.current_race:
                    st.markdown("### Step 2: Select or Create a Race")
                    meet_races_df = races_data[races_data["Meet_Name"] == st.session_state.current_meet]
                    existing_races = meet_races_df[meet_races_df["Race_Name"].astype(str).str.strip() != ""]["Race_Name"].dropna().unique().tolist()
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        if existing_races:
                            sel_race = st.selectbox("Choose Race", existing_races)
                            if st.button("Set Existing Race"):
                                st.session_state.current_race = sel_race
                                st.session_state.current_distance = meet_races_df[meet_races_df["Race_Name"] == sel_race]["Distance"].dropna().iloc[0]
                                st.rerun()
                    with col_r2:
                        new_race = st.text_input("New Race Category")
                        new_dist = st.selectbox("Distance", ["5K", "2 Mile", "Other"])
                        if st.button("Create New Race"):
                            if new_race:
                                st.session_state.current_race, st.session_state.current_distance = new_race, new_dist
                                st.rerun()

                elif st.session_state.current_meet and st.session_state.current_race:
                    col_info1, col_info2 = st.columns([3, 1])
                    with col_info1: st.info(f"Race Locked: {st.session_state.current_race} ({st.session_state.current_distance})")
                    with col_info2:
                        if st.button("Change Race"):
                            st.session_state.current_race = None
                            st.rerun()
                    st.markdown("---")
                    
                    active_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE") & (roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"]))].copy()
                    runner_dict = {row["Username"]: f"{row['First_Name']} {row['Last_Name']}" for _, row in active_athletes.sort_values(by=["Gender", "Last_Name"]).iterrows()}
                    
                    with st.form("add_race_result_form", clear_on_submit=True):
                        runner_selected = st.selectbox("Select Runner:", options=list(runner_dict.keys()), format_func=lambda x: runner_dict[x])
                        time_col1, time_col2, time_col3 = st.columns(3)
                        with time_col1: m1_time = st.text_input("Mile 1 Split")
                        with time_col2: m2_time = st.text_input("Mile 2 Split") if st.session_state.current_distance == "5K" else ""
                        with time_col3: total_time = st.text_input("Total Finish Time")
                            
                        if st.form_submit_button("Save Result"):
                            if total_time:
                                new_row = pd.DataFrame([{"Date": pd.to_datetime(st.session_state.current_meet_date).strftime("%Y-%m-%d"), "Meet_Name": st.session_state.current_meet, "Race_Name": st.session_state.current_race, "Distance": st.session_state.current_distance, "Username": runner_selected, "Mile_1": m1_time, "Mile_2": m2_time, "Total_Time": total_time, "Weight": 1.0}])
                                with st.spinner("Saving..."): conn.update(worksheet="Races", data=pd.concat([races_data, new_row], ignore_index=True))
                                st.cache_data.clear()
                                st.rerun()
                    
                    done_col1, done_col2 = st.columns(2)
                    with done_col1:
                        if st.button("Done with this Race", use_container_width=True): st.session_state.current_race = None; st.rerun()
                    with done_col2:
                        if st.button("Done with this Meet", use_container_width=True): st.session_state.current_meet, st.session_state.current_race = None, None; st.rerun()

            elif de_type == "Workouts":
                workout_action = st.radio("Action:", ["Log New Workout", "Edit/Delete Existing Workout"], horizontal=True)
                
                if workout_action == "Log New Workout":
                    if st.session_state["workout_saved"]:
                        st.success("Workout saved successfully to the database!")
                        if st.button("Log Another Workout"):
                            st.session_state["workout_saved"] = False
                            st.rerun()
                    else:
                        st.subheader("Workout Data Entry")
                        w_col1, w_col2, w_col3 = st.columns(3)
                        with w_col1:
                            w_date = st.date_input("Workout Date")
                            w_type = st.selectbox("Workout Type", ["Tempo", "Intervals", "Hills", "Other"])
                        with w_col2:
                            if w_type == "Tempo": dist_options = ["400m", "Miles", "Split", "Other"]
                            elif w_type == "Intervals": dist_options = ["400m", "800m", "1000m", "1200m", "1 Mile", "Custom/Other"]
                            elif w_type == "Hills": dist_options = ["400m", "800m", "Short Sprints", "Custom/Other"]
                            else: dist_options = ["Custom/Other"]
                            
                            selected_dist = st.selectbox("Distance/Rep Details", dist_options)
                            if selected_dist in ["Custom/Other", "Other", "Split"]: w_dist = st.text_input("Specify Distance/Details", placeholder="e.g., 2+1, 8x400m")
                            else: w_dist = selected_dist
                                
                            w_reps = st.number_input("Total Max Intervals/Segments Today", min_value=1, max_value=20, value=6)
                        with w_col3:
                            w_weather = st.text_input("Weather (Temp/Conditions)", placeholder="e.g., 75F, Humid")
                            calc_mode = st.radio("Time Entry Mode:", ["Individual Splits", "Continuous Clock (Elapsed)"], index=0)
                            restart_rep = 0
                            if calc_mode == "Continuous Clock (Elapsed)" and selected_dist == "Split":
                                restart_rep = st.number_input("Restart clock at Rep # (0 = never)", min_value=0, max_value=20, value=0, help="For a 2+1 split (3 total segments), set this to 3 so the 3rd column starts from 0.")

                        st.markdown("---")
                        
                        st.markdown("**Number-Only Entry Format**")
                        time_entry_format = st.radio(
                            "How should the app read numbers typed without a colon?",
                            ["Mins/Secs (e.g., 104 = 1:04, 530 = 5:30)", "Total Seconds (e.g., 82 = 1:22, 104 = 1:44)"],
                            horizontal=True,
                            help="This only applies if you type numbers without a colon to save time."
                        )
                        st.caption("Leave cells blank to skip an athlete. Select 'Not Assigned' to record they were intentionally excluded.")
                        
                        active_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE") & (roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"]))].copy()
                        active_athletes = active_athletes.sort_values(by=["Gender", "Last_Name"])
                        
                        grid_data = []
                        for _, row in active_athletes.iterrows():
                            entry = {"Username": row["Username"], "Athlete Name": f"{row['First_Name']} {row['Last_Name']}", "Status": "Present"}
                            for i in range(1, w_reps + 1): entry[f"Rep {i}"] = ""
                            grid_data.append(entry)
                        
                        df_grid = pd.DataFrame(grid_data)
                        
                        column_config = {
                            "Username": None,
                            "Athlete Name": st.column_config.TextColumn("Athlete Name", disabled=True),
                            "Status": st.column_config.SelectboxColumn("Status", options=["Present", "Not Assigned", "Sick", "Injured", "Unexcused"], required=True)
                        }
                        for i in range(1, w_reps + 1): column_config[f"Rep {i}"] = st.column_config.TextColumn(f"Rep {i}")

                        edited_df = st.data_editor(df_grid, hide_index=True, column_config=column_config, use_container_width=True, key="new_workout_editor")
                        
                        if st.button("Save Workout Data", type="primary"):
                            if not w_dist:
                                st.error("Please enter Distance/Rep Details before saving.")
                            else:
                                new_workout_rows = []
                                formatted_date = pd.to_datetime(w_date).strftime("%Y-%m-%d")
                                
                                for _, row in edited_df.iterrows():
                                    status = row["Status"]
                                    raw_times = [str(row[f"Rep {i}"]) for i in range(1, w_reps + 1) if str(row[f"Rep {i}"]).strip() != ""]
                                    
                                    if status != "Present" and len(raw_times) == 0:
                                        new_workout_rows.append({"Date": formatted_date, "Workout_Type": w_type, "Rep_Distance": w_dist, "Weather": w_weather, "Username": row["Username"], "Status": status, "Splits": ""})
                                        continue
                                    
                                    if len(raw_times) > 0:
                                        parsed_seconds = [time_to_seconds(parse_fast_time(t, time_entry_format)) for t in raw_times]
                                        final_splits = []
                                        
                                        if calc_mode == "Continuous Clock (Elapsed)":
                                            for i in range(len(parsed_seconds)):
                                                if i == 0 or (restart_rep > 0 and (i + 1) == restart_rep):
                                                    final_splits.append(seconds_to_time(parsed_seconds[i]))
                                                else:
                                                    final_splits.append(seconds_to_time(parsed_seconds[i] - parsed_seconds[i-1]))
                                        else:
                                            final_splits = [seconds_to_time(s) for s in parsed_seconds]
                                        
                                        split_string = ", ".join([s for s in final_splits if s != ""])
                                        new_workout_rows.append({"Date": formatted_date, "Workout_Type": w_type, "Rep_Distance": w_dist, "Weather": w_weather, "Username": row["Username"], "Status": status, "Splits": split_string})
                                
                                if new_workout_rows:
                                    updated_workouts = pd.concat([workouts_data, pd.DataFrame(new_workout_rows)], ignore_index=True)
                                    with st.spinner("Saving workout..."): conn.update(worksheet="Workouts", data=updated_workouts)
                                    st.session_state["workout_saved"] = True
                                    st.cache_data.clear()
                                    st.rerun()

                elif workout_action == "Edit/Delete Existing Workout":
                    st.subheader("Edit / Fix Existing Workout")
                    if workouts_data.empty or workouts_data["Date"].isna().all():
                        st.info("No workout data has been logged yet.")
                    else:
                        unique_workouts = workouts_data[["Date", "Workout_Type", "Rep_Distance"]].dropna(subset=["Date", "Workout_Type"]).drop_duplicates()
                        unique_workouts["Date_Obj"] = pd.to_datetime(unique_workouts["Date"], errors="coerce")
                        unique_workouts = unique_workouts.sort_values(by="Date_Obj", ascending=False)
                        
                        workout_options = {}
                        for _, row in unique_workouts.iterrows():
                            key = f"{row['Date']}|{row['Workout_Type']}"
                            try: nice_date = row["Date_Obj"].strftime("%b %d, %Y")
                            except: nice_date = str(row["Date"])
                            label = f"{nice_date} - {row['Workout_Type']} [{row.get('Rep_Distance', 'No Details')}]"
                            workout_options[key] = label
                            
                        if not workout_options:
                            st.info("No valid workouts found to edit.")
                        else:
                            selected_workout_key = st.selectbox("Select Workout to Edit:", options=list(workout_options.keys()), format_func=lambda x: workout_options[x])
                            
                            old_date, old_type = selected_workout_key.split("|")
                            target_rows = workouts_data[(workouts_data["Date"] == old_date) & (workouts_data["Workout_Type"] == old_type)].copy()
                            
                            if not target_rows.empty:
                                st.markdown("### Update Workout Details")
                                h_col1, h_col2 = st.columns(2)
                                
                                current_date_val = pd.to_datetime(target_rows.iloc[0]["Date"], errors="coerce").date()
                                current_type = target_rows.iloc[0]["Workout_Type"]
                                current_dist = target_rows.iloc[0]["Rep_Distance"]
                                current_weather = target_rows.iloc[0]["Weather"]
                                
                                type_options = ["Tempo", "Intervals", "Hills", "Other"]
                                t_index = type_options.index(current_type) if current_type in type_options else 3
                                
                                with h_col1:
                                    new_w_date = st.date_input("Workout Date", value=current_date_val)
                                    new_w_type = st.selectbox("Workout Type", type_options, index=t_index)
                                with h_col2:
                                    new_w_dist = st.text_input("Distance/Rep Details", value=current_dist)
                                    new_w_weather = st.text_input("Weather", value=current_weather)
                                
                                st.markdown("### Update Athlete Splits")
                                max_reps = 1
                                for _, r in target_rows.iterrows():
                                    splits = [s.strip() for s in str(r.get("Splits", "")).split(",") if s.strip()]
                                    if len(splits) > max_reps: max_reps = len(splits)
                                
                                grid_data = []
                                for _, r in target_rows.iterrows():
                                    roster_match = roster_data[roster_data["Username"] == r["Username"]]
                                    a_name = f"{roster_match.iloc[0]['First_Name']} {roster_match.iloc[0]['Last_Name']}" if not roster_match.empty else r["Username"]
                                    
                                    entry = {"Username": r["Username"], "Athlete Name": a_name, "Status": r["Status"]}
                                    splits = [s.strip() for s in str(r.get("Splits", "")).split(",") if s.strip()]
                                    
                                    for i in range(1, max_reps + 1):
                                        entry[f"Rep {i}"] = splits[i-1] if i <= len(splits) else ""
                                    grid_data.append(entry)
                                
                                df_grid = pd.DataFrame(grid_data)
                                
                                column_config = {
                                    "Username": None, 
                                    "Athlete Name": st.column_config.TextColumn("Athlete Name", disabled=True),
                                    "Status": st.column_config.SelectboxColumn("Status", options=["Present", "Not Assigned", "Sick", "Injured", "Unexcused"], required=True)
                                }
                                for i in range(1, max_reps + 1):
                                    column_config[f"Rep {i}"] = st.column_config.TextColumn(f"Rep {i}")

                                st.caption("Edit the splits below. Type the exact corrected time (e.g., 1:04).")
                                edited_df = st.data_editor(df_grid, hide_index=True, column_config=column_config, use_container_width=True, key="edit_workout_editor")
                                
                                col_save, col_del = st.columns(2)
                                with col_save:
                                    if st.button("💾 Save All Edits", type="primary", use_container_width=True):
                                        keep_rows = workouts_data[~((workouts_data["Date"] == old_date) & (workouts_data["Workout_Type"] == old_type))]
                                        formatted_new_date = pd.to_datetime(new_w_date).strftime("%Y-%m-%d")
                                        
                                        new_rows = []
                                        for _, row in edited_df.iterrows():
                                            status = row["Status"]
                                            raw_times = [str(row[f"Rep {i}"]).strip() for i in range(1, max_reps + 1) if str(row[f"Rep {i}"]).strip() != ""]
                                            
                                            split_string = ", ".join(raw_times)
                                            new_rows.append({
                                                "Date": formatted_new_date, "Workout_Type": new_w_type, "Rep_Distance": new_w_dist,
                                                "Weather": new_w_weather, "Username": row["Username"], "Status": status, "Splits": split_string
                                            })
                                            
                                        updated_workouts = pd.concat([keep_rows, pd.DataFrame(new_rows)], ignore_index=True)
                                        with st.spinner("Updating workout..."): conn.update(worksheet="Workouts", data=updated_workouts)
                                        st.success("Workout updated successfully!")
                                        st.cache_data.clear()
                                        st.rerun()
                                        
                                with col_del:
                                    if st.button("🗑️ Delete This Workout Entirely", use_container_width=True):
                                        keep_rows = workouts_data[~((workouts_data["Date"] == old_date) & (workouts_data["Workout_Type"] == old_type))]
                                        with st.spinner("Deleting workout..."): conn.update(worksheet="Workouts", data=keep_rows)
                                        st.success("Workout deleted!")
                                        st.cache_data.clear()
                                        st.rerun()

        with tab4:
            show_rankings_tab()

    # ----------------------------------
    # ATHLETE VIEW
    # ----------------------------------
    else:
        st.header("Training Dashboard")
        st.markdown("Your historical training and race data is below.")
        
        tab_dash, tab_rankings = st.tabs(["My Dashboard", "Team Rankings"])
        
        with tab_dash:
            user_races = races_data[races_data["Username"] == st.session_state["username"]].copy()
            user_workouts = workouts_data[workouts_data["Username"] == st.session_state["username"]].copy()
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric(label="Races Completed", value=len(user_races))
            col_m2.metric(label="Workouts Logged", value=len(user_workouts[user_workouts["Status"] == "Present"]))
            
            fastest_5k = "N/A"
            if not user_races.empty:
                five_k_races = user_races[user_races["Distance"].str.upper() == "5K"]
                if not five_k_races.empty:
                    fastest_sec = five_k_races["Total_Time"].apply(time_to_seconds).replace(0, float('inf')).min()
                    if fastest_sec != float('inf'): fastest_5k = seconds_to_time(fastest_sec)
                    
            col_m3.metric(label="5K PR (This Season)", value=fastest_5k)
            st.markdown("<br>", unsafe_allow_html=True)
            
            sub_races, sub_workouts = st.tabs(["Race Results", "Workouts"])
            with sub_races: display_athlete_races(st.session_state["username"])
            with sub_workouts: display_athlete_workouts(st.session_state["username"])
            
        with tab_rankings:
            show_rankings_tab()

# ==========================================
# --- 8. INITIALIZATION LOGIC ---
# ==========================================
if not st.session_state["logged_in"]: login_page()
elif st.session_state["first_login"]: password_reset_page()
else: home_page()
