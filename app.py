import streamlit as st
import pandas as pd
import datetime
import requests
import plotly.express as px  
from streamlit_gsheets import GSheetsConnection

# ==========================================
# --- 1. APP SETUP & VISUAL THEMES ---
# ==========================================
st.set_page_config(page_title="MCXC Team Dashboard", layout="centered")

MCXC_CRIMSON = "#8B2331"
MCXC_NAVY = "#0C223F"
MCXC_GOLD = "#C7B683"

THEMES = {
    "MCXC Classic (Light)": {
        "bar": f"linear-gradient(to right, {MCXC_CRIMSON}, {MCXC_NAVY}, {MCXC_GOLD})", 
        "metric_bg": "rgba(139, 35, 49, 0.05)", "metric_border": "rgba(139, 35, 49, 0.2)",
        "line": MCXC_CRIMSON, "app_bg": "#FFFFFF", "text": "#31333F", 
        "header": MCXC_NAVY, 
        "sidebar_bg": "#F0F2F6", "plotly_template": "plotly_white",
        "is_dark": False
    },
    "MCXC Elite (Dark)": {  
        "bar": f"linear-gradient(to right, {MCXC_CRIMSON}, {MCXC_GOLD}, {MCXC_CRIMSON})", 
        "metric_bg": "rgba(199, 182, 131, 0.1)", "metric_border": "rgba(199, 182, 131, 0.3)",
        "line": MCXC_GOLD, "app_bg": MCXC_NAVY, "text": "#F0F2F6", 
        "header": MCXC_GOLD, 
        "sidebar_bg": "#08182D", "plotly_template": "plotly_dark",
        "is_dark": True
    },
    "Midnight Runner (Dark)": {
        "bar": "linear-gradient(to right, #FF4B4B, #FF904F)", 
        "metric_bg": "rgba(255, 75, 75, 0.1)", "metric_border": "rgba(255, 75, 75, 0.3)",
        "line": "#FF4B4B", "app_bg": "#0E1117", "text": "#FFFFFF", 
        "header": MCXC_GOLD, 
        "sidebar_bg": "#1A1C24", "plotly_template": "plotly_dark",
        "is_dark": True
    },
    "Ocean Pace (Light)": {
        "bar": "linear-gradient(to right, #00C9FF, #92FE9D)", 
        "metric_bg": "rgba(0, 201, 255, 0.05)", "metric_border": "rgba(0, 201, 255, 0.3)",
        "line": "#00C9FF", "app_bg": "#F4F8FB", "text": "#1A2A3A", 
        "header": "#00C9FF",
        "sidebar_bg": "#E5F0F9", "plotly_template": "plotly_white",
        "is_dark": False
    }
}

if "theme" not in st.session_state:
    st.session_state["theme"] = "MCXC Classic (Light)"

current_theme = THEMES[st.session_state["theme"]]

dark_mode_css = ""
if current_theme["is_dark"]:
    dark_mode_css = f"""
        [data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-baseweb="base-input"] {{
            background-color: rgba(0,0,0,0.4) !important;
            color: #FFFFFF !important;
            border-color: rgba(255,255,255,0.2) !important;
        }}
        [data-testid="stForm"] {{
            background-color: {current_theme['sidebar_bg']} !important;
            border-color: rgba(255,255,255,0.1) !important;
        }}
        input, textarea, select {{
            color: #FFFFFF !important;
        }}
        [data-testid="stDataFrame"], [data-testid="stDataEditor"] {{
            filter: invert(0.92) hue-rotate(180deg);
        }}
    """

st.markdown(f"""
    <style>
        .stApp {{
            background-color: {current_theme['app_bg']} !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: {current_theme['sidebar_bg']} !important;
        }}
        [data-testid="stHeader"] {{
            background-color: transparent !important;
        }}
        .color-bar {{
            height: 8px;
            background: {current_theme['bar']};
            margin-bottom: 2rem;
            border-radius: 4px;
        }}
        div[data-testid="metric-container"] {{
            background-color: {current_theme['metric_bg']} !important;
            border: 1px solid {current_theme['metric_border']} !important;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        h1, h2, h3, h4, h5, h6,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
            color: {current_theme['header']} !important;
        }}

        .stMarkdown p, .stMarkdown li, .stMarkdown span, div[data-testid="stCaptionContainer"],
        label, .stMetricValue, div[data-testid="stTabs"] button p {{
            color: {current_theme['text']} !important;
        }}
        
        div.stButton > button, div.stFormSubmitButton > button {{
            background-color: {current_theme['sidebar_bg']} !important;
            color: {current_theme['text']} !important;
            border: 1px solid {current_theme['metric_border']} !important;
            transition: all 0.3s ease;
        }}
        
        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            border-color: {current_theme['line']} !important;
            color: {current_theme['line']} !important;
            background-color: {current_theme['app_bg']} !important;
        }}
        
        /* ==========================================
           PRINT CSS (Hides UI Elements for clean printing)
           ========================================== */
        @media print {{
            .stApp {{ background-color: white !important; }}
            section[data-testid="stSidebar"], header[data-testid="stHeader"], 
            div[data-testid="stToolbar"], div[data-testid="stDecoration"] {{ display: none !important; }}
            
            .stRadio, .stSelectbox, .stButton, .stMultiSelect, .stNumberInput, .stTextInput {{ display: none !important; }}
            div[data-testid="stForm"] {{ display: none !important; }}
            div[data-testid="stTabs"] > div:first-child {{ display: none !important; }}
            
            .stMainBlockContainer {{ max-width: 100% !important; padding: 0 !important; }}
            h1, h2, h3, h4, h5, h6, p, span, div, td, th {{ color: black !important; }}
            
            .print-table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; page-break-inside: avoid; font-size: 14px; }}
            .print-table th, .print-table td {{ border: 1px solid black !important; padding: 8px; text-align: left; }}
            .print-table th {{ background-color: #e2e8f0 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; font-weight: bold; }}
            .color-bar {{ display: none !important; }}
        }}
        
        {dark_mode_css}
    </style>
    <div class="color-bar"></div>
""", unsafe_allow_html=True)

# ==========================================
# --- 2. MATH, LOGIC, & WEATHER ---
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

def calculate_season(date_val):
    try:
        d = pd.to_datetime(date_val)
        if pd.isna(d): return str(datetime.date.today().year)
        return str(d.year) if d.month >= 7 else str(d.year - 1)
    except:
        return str(datetime.date.today().year)

CURRENT_SEASON = calculate_season(datetime.date.today())

@st.cache_data(ttl=86400) 
def get_weather_for_date(date_str):
    LATITUDE = 34.077604
    LONGITUDE = -83.877289
    
    try:
        d_obj = pd.to_datetime(date_str)
        d = d_obj.strftime('%Y-%m-%d')
        days_ago = (pd.to_datetime("today") - d_obj).days
        
        if days_ago > 60:
            url = f"https://archive-api.open-meteo.com/v1/archive?latitude={LATITUDE}&longitude={LONGITUDE}&start_date={d}&end_date={d}&daily=temperature_2m_max,precipitation_sum&temperature_unit=fahrenheit&precipitation_unit=inch&timezone=America/New_York"
        else:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&start_date={d}&end_date={d}&daily=temperature_2m_max,precipitation_sum&temperature_unit=fahrenheit&precipitation_unit=inch&timezone=America/New_York"
            
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            temp = data.get('daily', {}).get('temperature_2m_max', [None])[0]
            precip = data.get('daily', {}).get('precipitation_sum', [None])[0]
            
            if temp is None:
                return "Can't access weather data"
                
            desc = f"{round(temp)}°F"
            if precip and precip > 0.05:
                desc += f" ({round(precip, 1)}in Rain)"
            else:
                desc += " (Dry)"
            return desc
        return "Can't access weather data"
    except Exception as e:
        return "Can't access weather data"

# ==========================================
# --- 3. DATABASE CONNECTION & CLEANUP ---
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

roster_data = conn.read(worksheet="Roster", ttl=600).dropna(how="all")
races_data = conn.read(worksheet="Races", ttl=600).dropna(how="all")
workouts_data = conn.read(worksheet="Workouts", ttl=600).dropna(how="all")

if "Username" in roster_data.columns:
    roster_data = roster_data[roster_data["Username"].astype(str).str.strip() != ""]
    roster_data = roster_data.dropna(subset=["Username"])

if "Username" in races_data.columns:
    races_data = races_data[races_data["Username"].astype(str).str.strip() != ""]
    races_data = races_data.dropna(subset=["Username"])

if "Username" in workouts_data.columns:
    workouts_data = workouts_data[workouts_data["Username"].astype(str).str.strip() != ""]
    workouts_data = workouts_data.dropna(subset=["Username"])

if "Active" in roster_data.columns: 
    roster_data["Active_Clean"] = roster_data["Active"].astype(str).str.strip().str.upper()
else: 
    roster_data["Active_Clean"] = "TRUE"
    
if "Gender" not in roster_data.columns: 
    roster_data["Gender"] = "N/A"

expected_race_cols = ["Date", "Meet_Name", "Race_Name", "Distance", "Username", "Mile_1", "Mile_2", "Total_Time", "Weight", "Active"]
for col in expected_race_cols:
    if col not in races_data.columns: 
        if col == "Weight": races_data[col] = 1.0
        elif col == "Active": races_data[col] = "TRUE"
        else: races_data[col] = ""

races_data["Weight"] = pd.to_numeric(races_data["Weight"], errors="coerce").fillna(1.0)
races_data["Active"] = races_data["Active"].astype(str).str.strip().str.upper()
races_data.loc[races_data["Active"] == "NAN", "Active"] = "TRUE"
races_data.loc[races_data["Active"] == "", "Active"] = "TRUE"

expected_workout_cols = ["Date", "Workout_Type", "Rep_Distance", "Weather", "Username", "Status", "Splits"]
for col in expected_workout_cols:
    if col not in workouts_data.columns: 
        workouts_data[col] = ""

races_data["Season"] = races_data["Date"].apply(calculate_season)
workouts_data["Season"] = workouts_data["Date"].apply(calculate_season)

# ==========================================
# --- 4. SESSION STATE MANAGEMENT ---
# ==========================================
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
    
    r_col1, r_col2, r_col3 = st.columns(3)
    
    available_seasons = sorted(races_data["Season"].unique().tolist(), reverse=True)
    if not available_seasons: available_seasons = [CURRENT_SEASON]
    with r_col1: r_season = st.selectbox("Season", available_seasons, key="rankings_season")
    with r_col2: r_gender = st.selectbox("Category", ["Men's", "Women's"], key="rankings_category")
    with r_col3: r_dist = st.selectbox("Distance", ["5K", "2 Mile"], key="rankings_distance")
        
    target_gender = "Male" if r_gender == "Men's" else "Female"
    
    merged = pd.merge(races_data, roster_data[["Username", "First_Name", "Last_Name", "Gender", "Active_Clean"]], on="Username", how="inner")
    
    merged = merged[merged["Active_Clean"].isin(["TRUE", "1", "1.0"])]
    merged = merged[merged["Active"].isin(["TRUE", "1", "1.0"])]
    merged = merged[(merged["Gender"].str.title() == target_gender) & (merged["Distance"].str.upper() == r_dist.upper()) & (merged["Season"] == r_season)]
    
    if merged.empty:
        st.info("No active race data found for this category and season.")
        return
    
    tab_lead, tab_grid = st.tabs(["Leaderboard", "Master Grid"])
    
    with tab_lead:
        r_metric = st.radio("Rank By:", ["Weighted Average", "Personal Record (PR)"], horizontal=True, key="rankings_metric")
        
        merged["Time_Sec"] = merged["Total_Time"].apply(time_to_seconds)
        merged["Weight"] = pd.to_numeric(merged["Weight"], errors="coerce").fillna(1.0)
        
        results = []
        for user, group in merged.groupby("Username"):
            valid_races = group[group["Weight"] > 0] 
            if valid_races.empty: continue
                
            if r_metric == "Personal Record (PR)":
                best_time = valid_races["Time_Sec"].min()
                results.append({"Athlete": f"{group.iloc[0]['First_Name']} {group.iloc[0]['Last_Name']}", "Time_Sec": best_time, "Mark": seconds_to_time(best_time)})
            else: 
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
        
        grid_df["Date_Obj"] = pd.to_datetime(grid_df["Date"], errors='coerce')
        grid_df = grid_df.sort_values(by="Date_Obj")
        
        grid_df["Race_Col"] = grid_df["Meet_Name"] + " (" + grid_df["Date_Obj"].dt.strftime('%m/%d').fillna("") + ")"
        
        ordered_cols = grid_df["Race_Col"].unique().tolist()
        
        pivot_df = grid_df.pivot_table(index="Athlete", columns="Race_Col", values="Total_Time", aggfunc="first")
        pivot_df = pivot_df.reindex(columns=ordered_cols).fillna("-").reset_index()
        
        st.dataframe(pivot_df, hide_index=True, use_container_width=True)

def plot_athlete_progress(user_races):
    df = user_races[(user_races["Distance"].str.upper() == "5K") & (user_races["Time_Sec"] > 0)].copy()
    if df.empty or len(df) < 2:
        return 
    
    df["Date_Obj"] = pd.to_datetime(df["Date"], errors='coerce')
    df = df.sort_values("Date_Obj")
    df["Time_Min"] = df["Time_Sec"] / 60.0  
    
    fig = px.line(
        df, x="Date_Obj", y="Time_Min", markers=True, 
        title="📈 5K Progression",
        hover_data={"Date_Obj": "|%b %d, %Y", "Time_Min": False, "Total_Time": True, "Meet_Name": True}
    )
    
    fig.update_yaxes(title="Finish Time (Minutes)", autorange="reversed")
    fig.update_xaxes(title="Race Date")
    fig.update_layout(template=THEMES[st.session_state["theme"]]["plotly_template"])
    
    theme_line_color = THEMES[st.session_state["theme"]]["line"]
    fig.update_traces(line_color=theme_line_color, line_width=3, marker_size=8)
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

def display_athlete_races(target_username, target_season):
    user_races = races_data[(races_data["Username"] == target_username) & (races_data["Active"].isin(["TRUE", "1", "1.0"])) & (races_data["Season"] == target_season)].copy()
    if not user_races.empty:
        user_races["Time_Sec"] = user_races["Total_Time"].apply(time_to_seconds)
        user_races = user_races[user_races["Time_Sec"] > 0] 
        
        user_races["Date_Obj"] = pd.to_datetime(user_races["Date"], errors='coerce')
        user_races = user_races.sort_values(by="Date_Obj", ascending=True)
        
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
        user_races["Date"] = user_races["Date_Obj"].dt.strftime('%m/%d/%Y').fillna("Unknown")
        
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
        st.info("No active race data found for this season.")

def display_athlete_workouts(target_username, target_season):
    user_workouts = workouts_data[(workouts_data["Username"] == target_username) & (workouts_data["Season"] == target_season)].copy()
    if not user_workouts.empty:
        user_workouts["Date_Obj"] = pd.to_datetime(user_workouts["Date"], errors='coerce')
        user_workouts = user_workouts.sort_values(by="Date_Obj", ascending=False)
        
        for idx, row in user_workouts.iterrows():
            if pd.isna(row["Weather"]) or str(row["Weather"]).strip() == "":
                user_workouts.at[idx, "Weather"] = get_weather_for_date(row["Date"])
                
        user_workouts["Date"] = user_workouts["Date_Obj"].dt.strftime('%m/%d/%Y').fillna("Unknown")
        
        display_cols = ["Date", "Workout_Type", "Rep_Distance", "Status", "Splits", "Weather"]
        rename_dict = {"Workout_Type": "Type", "Rep_Distance": "Details"}
        clean_table = user_workouts[display_cols].rename(columns=rename_dict)
        st.dataframe(clean_table, hide_index=True, use_container_width=True)
    else:
        st.info("No workout data found for this season.")

# ==========================================
# --- 6. LOGIN & SECURITY PAGES ---
# ==========================================
def login_page():
    st.title("MCXC Team Dashboard")
    st.markdown("Please log in to access your training data.")
    with st.form("login_form"):
        username = st.text_input("Username", autocomplete="off")
        password = st.text_input("Password", type="password", autocomplete="new-password")
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
        new_password = st.text_input("New Password", type="password", autocomplete="new-password")
        confirm_password = st.text_input("Confirm New Password", type="password", autocomplete="new-password")
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
    
    with st.sidebar:
        st.subheader("⚙️ Settings")
        selected_theme = st.selectbox("App Theme", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state["theme"]))
        if selected_theme != st.session_state["theme"]:
            st.session_state["theme"] = selected_theme
            st.rerun()
        st.markdown("---")
        st.button("Log Out", on_click=logout, use_container_width=True)
    
    st.title(f"{user_role}: {st.session_state['first_name']} {st.session_state['last_name']}")
    st.markdown("---")
    
    if user_role.upper() == "COACH":
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Athlete Lookup", "Roster Management", "Data Entry", "Team Rankings", "Meet Setup & Printables"])
        
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
                    
                    u_races = races_data[races_data["Username"] == selected_username]
                    u_works = workouts_data[workouts_data["Username"] == selected_username]
                    athlete_seasons = sorted(list(set(u_races["Season"].tolist() + u_works["Season"].tolist())), reverse=True)
                    if not athlete_seasons: athlete_seasons = [CURRENT_SEASON]
                    
                    sel_season = st.selectbox("View Season:", athlete_seasons, key="coach_athlete_season")
                    
                    sub_tab1, sub_tab2 = st.tabs(["Race Results", "Workouts"])
                    with sub_tab1: display_athlete_races(selected_username, sel_season)
                    with sub_tab2: display_athlete_workouts(selected_username, sel_season)
                
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
                    with r1_col1: new_first = st.text_input("First Name", autocomplete="off")
                    with r1_col2: new_last = st.text_input("Last Name", autocomplete="off")
                    r2_col1, r2_col2 = st.columns(2)
                    with r2_col1: new_role = st.selectbox("Role", ["Athlete", "Coach"])
                    with r2_col2: new_grad_year = st.text_input("Grad Year (e.g., 2028)", autocomplete="off")
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
                            with e1_col1: edit_first = st.text_input("First Name", value=target_row["First_Name"], autocomplete="off")
                            with e1_col2: edit_last = st.text_input("Last Name", value=target_row["Last_Name"], autocomplete="off")
                            e2_col1, e2_col2 = st.columns(2)
                            with e2_col1:
                                role_index = 0 if str(target_row["Role"]).title() == "Athlete" else 1
                                edit_role = st.selectbox("Role", ["Athlete", "Coach"], index=role_index)
                            with e2_col2: edit_grad_year = st.text_input("Grad Year", value=str(target_row.get("Grad_Year", "")), autocomplete="off")
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
            de_type = st.radio("Select Entry Mode", ["Race Results", "Workouts", "Manage Meet Weights", "Archive Specific Meet"], horizontal=True)
            st.markdown("---")
            
            if de_type == "Archive Specific Meet":
                st.subheader("Archive a Single Meet")
                st.markdown("Hiding a meet from the active dashboard (e.g. if you entered fake data or want to hide a specific event). Data remains in the database.")
                
                active_races_mask = races_data["Active"].isin(["TRUE", "1", "1.0"])
                active_meets = races_data[active_races_mask][["Meet_Name", "Date"]].drop_duplicates()
                
                if active_meets.empty:
                    st.info("No active meets available to archive.")
                else:
                    meet_options = {f"{row['Meet_Name']}|{row['Date']}": f"{pd.to_datetime(row['Date'], errors='coerce').strftime('%m/%d/%Y')} | {row['Meet_Name']}" for _, row in active_meets.iterrows()}
                    with st.form("archive_meet_form"):
                        meet_to_archive = st.selectbox("Select Meet", options=list(meet_options.keys()), format_func=lambda x: meet_options[x])
                        if st.form_submit_button("Archive Meet"):
                            m_name, m_date = meet_to_archive.split("|")
                            mask = (races_data["Meet_Name"] == m_name) & (races_data["Date"] == m_date)
                            races_data.loc[mask, "Active"] = "FALSE"
                            with st.spinner("Archiving..."):
                                conn.update(worksheet="Races", data=races_data)
                            st.success(f"Archived {m_name}!")
                            st.cache_data.clear()
                            st.rerun()

            elif de_type == "Manage Meet Weights":
                st.subheader("Manage Meet Multipliers & Weights")
                st.info(f"Currently managing weights for the **{CURRENT_SEASON}** season.")
                
                active_races = races_data[(races_data["Active"].isin(["TRUE", "1", "1.0"])) & (races_data["Season"] == CURRENT_SEASON)]
                unique_meets = active_races[["Meet_Name", "Date", "Weight"]].drop_duplicates(subset=["Meet_Name", "Date"])
                
                if unique_meets.empty or unique_meets["Meet_Name"].isna().all(): 
                    st.info("No meets logged yet for the current season.")
                else:
                    with st.form("weights_form"):
                        updated_weights = {}
                        for index, row in unique_meets.iterrows():
                            meet = row["Meet_Name"]
                            date = row["Date"]
                            current_w = row["Weight"]
                            label = f"{pd.to_datetime(date, errors='coerce').strftime('%m/%d/%Y')} | {meet}"
                            
                            new_w = st.number_input(label, value=float(current_w), step=0.5, min_value=0.0, key=f"weight_input_{index}")
                            updated_weights[(meet, date)] = new_w
                            
                        if st.form_submit_button("Save Weights", type="primary"):
                            for (m, d), w in updated_weights.items():
                                mask = (races_data["Meet_Name"] == m) & (races_data["Date"] == d)
                                races_data.loc[mask, "Weight"] = w
                                
                            with st.spinner("Updating database..."): 
                                conn.update(worksheet="Races", data=races_data)
                            st.success("Meet Weights updated successfully!")
                            st.cache_data.clear()
                            st.rerun()

            elif de_type == "Race Results":
                st.subheader("Race Data Entry")
                st.markdown("Select an existing meet to enter times in bulk. *(Note: To create a new meet, go to the **Meet Setup & Printables** tab!)*")

                active_races = races_data[races_data["Active"].isin(["TRUE", "1", "1.0"])]
                existing_meets = active_races["Meet_Name"].dropna().unique().tolist()

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    sel_meet = st.selectbox("1. Choose Meet", ["-- Select --"] + existing_meets)
                with col_m2:
                    if sel_meet != "-- Select --":
                        meet_races = active_races[active_races["Meet_Name"] == sel_meet]["Race_Name"].dropna().unique().tolist()
                        sel_race = st.selectbox("2. Choose Race", ["-- Select --"] + meet_races)
                    else:
                        sel_race = "-- Select --"

                if sel_meet != "-- Select --" and sel_race != "-- Select --":
                    st.markdown("---")
                    target_rows = active_races[(active_races["Meet_Name"] == sel_meet) & (active_races["Race_Name"] == sel_race)].copy()

                    all_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE") & (roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"]))]
                    unassigned = all_athletes[~all_athletes["Username"].isin(target_rows["Username"])]
                    un_opts = {row["Username"]: f"{row['First_Name']} {row['Last_Name']}" for _, row in unassigned.sort_values(by="Last_Name").iterrows()}

                    if un_opts:
                        with st.expander("➕ Add Walk-On / Missing Runners to this Race"):
                            add_runners = st.multiselect("Select Runners:", options=list(un_opts.keys()), format_func=lambda x: un_opts[x])
                            if st.button("Add to Race Roster"):
                                date_val = target_rows["Date"].iloc[0] if not target_rows.empty else pd.to_datetime("today").strftime("%Y-%m-%d")
                                dist_val = target_rows["Distance"].iloc[0] if not target_rows.empty else "5K"
                                season = calculate_season(date_val)
                                new_r = []
                                for uname in add_runners:
                                    new_r.append({
                                        "Date": date_val, "Meet_Name": sel_meet, "Race_Name": sel_race,
                                        "Distance": dist_val, "Username": uname, "Mile_1": "", "Mile_2": "",
                                        "Total_Time": "", "Weight": 1.0, "Active": "TRUE", "Season": season
                                    })
                                updated = pd.concat([races_data, pd.DataFrame(new_r)], ignore_index=True)
                                with st.spinner("Adding runners..."): conn.update(worksheet="Races", data=updated)
                                st.cache_data.clear()
                                st.rerun()

                    st.markdown(f"### {sel_race} Results")
                    grid_data = []
                    for _, r in target_rows.iterrows():
                        roster_match = roster_data[roster_data["Username"] == r["Username"]]
                        a_name = f"{roster_match.iloc[0]['First_Name']} {roster_match.iloc[0]['Last_Name']}" if not roster_match.empty else r["Username"]
                        grid_data.append({
                            "Username": r["Username"], "Athlete Name": a_name,
                            "Mile 1": r.get("Mile_1", ""), "Mile 2": r.get("Mile_2", ""), "Total Time": r.get("Total_Time", "")
                        })

                    df_grid = pd.DataFrame(grid_data)
                    col_config = {
                        "Username": None,
                        "Athlete Name": st.column_config.TextColumn("Athlete Name", disabled=True),
                        "Mile 1": st.column_config.TextColumn("Mile 1 Split"),
                        "Mile 2": st.column_config.TextColumn("Mile 2 Split"),
                        "Total Time": st.column_config.TextColumn("Total Finish Time")
                    }

                    st.caption("Type times exactly as you want them to appear (e.g., 18:45). Runners left blank will be ignored in rankings.")
                    edited_df = st.data_editor(df_grid, hide_index=True, column_config=col_config, use_container_width=True, key="race_results_editor")

                    col_save, col_del = st.columns(2)
                    with col_save:
                        if st.button("💾 Save All Race Results", type="primary", use_container_width=True):
                            for _, row in edited_df.iterrows():
                                mask = (races_data["Meet_Name"] == sel_meet) & (races_data["Race_Name"] == sel_race) & (races_data["Username"] == row["Username"])
                                races_data.loc[mask, "Mile_1"] = str(row["Mile 1"]).strip() if pd.notna(row["Mile 1"]) else ""
                                races_data.loc[mask, "Mile_2"] = str(row["Mile 2"]).strip() if pd.notna(row["Mile 2"]) else ""
                                races_data.loc[mask, "Total_Time"] = str(row["Total Time"]).strip() if pd.notna(row["Total Time"]) else ""

                            with st.spinner("Saving results..."): conn.update(worksheet="Races", data=races_data)
                            st.success("Results updated!")
                            st.cache_data.clear()
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ Delete Entire Race", use_container_width=True):
                            keep_rows = races_data[~((races_data["Meet_Name"] == sel_meet) & (races_data["Race_Name"] == sel_race))]
                            with st.spinner("Deleting..."): conn.update(worksheet="Races", data=keep_rows)
                            st.success("Race deleted.")
                            st.cache_data.clear()
                            st.rerun()

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
                            if selected_dist in ["Custom/Other", "Other", "Split"]: w_dist = st.text_input("Specify Distance/Details", placeholder="e.g., 2+1, 8x400m", autocomplete="off")
                            else: w_dist = selected_dist
                                
                            w_reps = st.number_input("Total Max Intervals/Segments Today", min_value=1, max_value=20, value=6)
                        with w_col3:
                            calc_mode = st.radio("Time Entry Mode:", ["Individual Splits", "Continuous Clock (Elapsed)"], index=0)
                            restart_rep = 0
                            if calc_mode == "Continuous Clock (Elapsed)" and selected_dist == "Split":
                                restart_rep = st.number_input("Restart clock at Rep # (0 = never)", min_value=0, max_value=20, value=0, help="For a 2+1 split (3 total segments), set this to 3 so the 3rd column starts from 0.")

                        st.markdown("---")
                        
                        st.markdown("**Number-Only Entry Format**")
                        time_entry_format = st.radio(
                            "How should the app read numbers typed without a colon?",
                            ["Mins/Secs (e.g., 104 = 1:04, 530 = 5:30)", "Total Seconds (e.g., 82 = 1:22, 104 = 1:44)"],
                            horizontal=True
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
                                
                                w_weather = get_weather_for_date(formatted_date)
                                season = calculate_season(formatted_date)
                                
                                for _, row in edited_df.iterrows():
                                    status = row["Status"]
                                    raw_times = [str(row[f"Rep {i}"]) for i in range(1, w_reps + 1) if str(row[f"Rep {i}"]).strip() != ""]
                                    
                                    if status != "Present" and len(raw_times) == 0:
                                        new_workout_rows.append({"Date": formatted_date, "Workout_Type": w_type, "Rep_Distance": w_dist, "Weather": w_weather, "Username": row["Username"], "Status": status, "Splits": "", "Season": season})
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
                                        new_workout_rows.append({"Date": formatted_date, "Workout_Type": w_type, "Rep_Distance": w_dist, "Weather": w_weather, "Username": row["Username"], "Status": status, "Splits": split_string, "Season": season})
                                
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
                                    st.markdown(f"**Current Weather:** {current_weather}")
                                with h_col2:
                                    new_w_dist = st.text_input("Distance/Rep Details", value=current_dist, autocomplete="off")
                                
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
                                        season = calculate_season(formatted_new_date)
                                        
                                        if formatted_new_date != old_date or not current_weather or "Can't" in current_weather:
                                            final_weather = get_weather_for_date(formatted_new_date)
                                        else:
                                            final_weather = current_weather
                                            
                                        new_rows = []
                                        for _, row in edited_df.iterrows():
                                            status = row["Status"]
                                            raw_times = [str(row[f"Rep {i}"]).strip() for i in range(1, max_reps + 1) if str(row[f"Rep {i}"]).strip() != ""]
                                            
                                            split_string = ", ".join(raw_times)
                                            new_rows.append({
                                                "Date": formatted_new_date, "Workout_Type": new_w_type, "Rep_Distance": new_w_dist,
                                                "Weather": final_weather, "Username": row["Username"], "Status": status, "Splits": split_string, "Season": season
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
            
        with tab5:
            st.subheader("🖨️ Meet Setup & Printables")
            print_action = st.radio("Select Tool:", ["Attendance Sheet", "Create New Meet / Print Sheet", "Re-Print Existing Meet"], horizontal=True)
            st.markdown("---")
            
            if print_action == "Attendance Sheet":
                col_a1, col_a2, col_a3 = st.columns(3)
                with col_a1: p_gender = st.selectbox("Team", ["Boys", "Girls"])
                with col_a2: p_type = st.selectbox("Season Type", ["Summer", "School Year"])
                with col_a3: p_week = st.text_input("Week Of (e.g., Aug 12 - 16)")
                
                if st.button("Generate Attendance Sheet", type="primary"):
                    active_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE") & (roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"]))].copy()
                    target_gender = "Male" if p_gender == "Boys" else "Female"
                    active_athletes = active_athletes[active_athletes["Gender"].str.title() == target_gender].sort_values(by="Last_Name")
                    
                    if p_type == "Summer":
                        cols = ["Mon In", "Mon Out", "Tues In", "Tues Out", "Thur In", "Thur Out"]
                    else:
                        cols = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                        
                    html = f"<h2>{p_gender.upper()} {p_type.upper()} ATTENDANCE</h2>"
                    if p_week: html += f"<h3>WEEK OF: {p_week}</h3>"
                    
                    html += "<table class='print-table'><tr><th>Runner</th>"
                    for c in cols: html += f"<th>{c}</th>"
                    html += "</tr>"
                    
                    for _, row in active_athletes.iterrows():
                        html += f"<tr><td>{row['Last_Name']}, {row['First_Name']}</td>"
                        for _ in cols: html += "<td></td>"
                        html += "</tr>"
                    html += "</table>"
                    
                    st.info("Press **Ctrl+P** (or **Cmd+P** on Mac) to print. All menus and buttons will automatically hide on the printed page!")
                    st.markdown(html, unsafe_allow_html=True)

            elif print_action == "Create New Meet / Print Sheet":
                st.markdown("Build your race entries here to instantly generate a printable clipboard sheet AND save the pending roster to the database for ultra-fast post-race data entry.")
                
                c_m1, c_m2 = st.columns(2)
                with c_m1: p_meet = st.text_input("New Meet Name", placeholder="e.g. Asics Invitational", autocomplete="off")
                with c_m2: p_date = st.date_input("Meet Date")
                
                st.markdown("---")
                race_count = st.number_input("How many separate races do you need?", min_value=1, max_value=10, value=2)
                
                active_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE") & (roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"]))].copy()
                athlete_opts = {row["Username"]: f"{row['First_Name']} {row['Last_Name']}" for _, row in active_athletes.sort_values(by=["Gender", "Last_Name"]).iterrows()}
                
                races_to_print = []
                for i in range(race_count):
                    st.markdown(f"**Race Block {i+1}**")
                    r_col1, r_col2, r_col3 = st.columns([2, 1, 3])
                    with r_col1:
                        r_name = st.text_input("Race Title", placeholder="e.g. Boys Champ", key=f"rname_{i}", autocomplete="off")
                    with r_col2:
                        r_dist = st.selectbox("Distance", ["5K", "2 Mile", "Other"], key=f"rdist_{i}")
                    with r_col3:
                        r_runners = st.multiselect("Select Runners", options=list(athlete_opts.keys()), format_func=lambda x: athlete_opts[x], key=f"rrunners_{i}")
                    if r_name and r_runners:
                        races_to_print.append({"name": r_name, "dist": r_dist, "runners": r_runners})
                    st.markdown("<br>", unsafe_allow_html=True)
                        
                if st.button("Generate Sheet & Save Meet Setup", type="primary"):
                    if not p_meet:
                        st.error("Please enter a Meet Name.")
                    elif not races_to_print:
                        st.warning("Please configure at least one race with runners.")
                    else:
                        formatted_date = pd.to_datetime(p_date).strftime("%Y-%m-%d")
                        season = calculate_season(formatted_date)
                        
                        new_rows = []
                        for race in races_to_print:
                            for uname in race['runners']:
                                existing = races_data[(races_data["Meet_Name"] == p_meet) & (races_data["Race_Name"] == race['name']) & (races_data["Username"] == uname)]
                                if existing.empty:
                                    new_rows.append({
                                        "Date": formatted_date, "Meet_Name": p_meet, "Race_Name": race['name'],
                                        "Distance": race['dist'], "Username": uname, "Mile_1": "", "Mile_2": "",
                                        "Total_Time": "", "Weight": 1.0, "Active": "TRUE", "Season": season
                                    })
                        if new_rows:
                            updated_races = pd.concat([races_data, pd.DataFrame(new_rows)], ignore_index=True)
                            with st.spinner("Saving to database..."): conn.update(worksheet="Races", data=updated_races)
                            st.cache_data.clear()
                            
                        st.success(f"Successfully created '{p_meet}'! You can enter finish times in the 'Data Entry' tab after the race.")
                        st.info("Press **Ctrl+P** (or **Cmd+P** on Mac) to print. All menus and buttons will automatically hide on the printed page!")
                        
                        html = f"<h2>{p_meet} - Split Sheet</h2>"
                        for race in races_to_print:
                            html += f"<h3>{race['name']} ({race['dist']})</h3>"
                            html += "<table class='print-table'>"
                            html += "<tr><th>Athlete</th><th>Prior Best at Meet</th><th>1 Mile</th><th>2 Mile</th><th>Finish</th></tr>"
                            
                            for uname in race['runners']:
                                a_name = athlete_opts[uname]
                                prior_time = ""
                                
                                prior_races = races_data[(races_data["Username"] == uname) & (races_data["Meet_Name"] == p_meet) & (races_data["Total_Time"].str.strip() != "")]
                                if not prior_races.empty:
                                    prior_races["Time_Sec"] = prior_races["Total_Time"].apply(time_to_seconds)
                                    prior_races = prior_races[prior_races["Time_Sec"] > 0]
                                    if not prior_races.empty:
                                        prior_time = seconds_to_time(prior_races["Time_Sec"].min())
                                
                                if not prior_time:
                                    all_5k = races_data[(races_data["Username"] == uname) & (races_data["Distance"].str.upper() == "5K") & (races_data["Total_Time"].str.strip() != "")]
                                    if not all_5k.empty:
                                        all_5k["Time_Sec"] = all_5k["Total_Time"].apply(time_to_seconds)
                                        all_5k = all_5k[all_5k["Time_Sec"] > 0]
                                        if not all_5k.empty:
                                            prior_time = f"{seconds_to_time(all_5k['Time_Sec'].min())} (PR)"
                                
                                html += f"<tr><td>{a_name}</td><td>{prior_time}</td><td></td><td></td><td></td></tr>"
                            html += "</table><br>"
                            
                        st.markdown(html, unsafe_allow_html=True)
                        
            elif print_action == "Re-Print Existing Meet":
                active_meets = races_data[races_data["Active"].isin(["TRUE", "1", "1.0"])]["Meet_Name"].dropna().unique().tolist()
                p_meet = st.selectbox("Select Existing Meet to Print", ["-- Select Meet --"] + active_meets)
                
                if p_meet != "-- Select Meet --":
                    if st.button("Generate Print Sheet", type="primary"):
                        st.info("Press **Ctrl+P** (or **Cmd+P** on Mac) to print.")
                        meet_rows = races_data[races_data["Meet_Name"] == p_meet]
                        unique_races = meet_rows["Race_Name"].unique()
                        
                        active_athletes = roster_data[(roster_data["Role"].str.upper() == "ATHLETE")].copy()
                        athlete_opts = {row["Username"]: f"{row['First_Name']} {row['Last_Name']}" for _, row in active_athletes.iterrows()}

                        html = f"<h2>{p_meet} - Split Sheet</h2>"
                        for r_name in unique_races:
                            r_rows = meet_rows[meet_rows["Race_Name"] == r_name]
                            dist = r_rows["Distance"].iloc[0] if not r_rows.empty else ""
                            html += f"<h3>{r_name} ({dist})</h3>"
                            html += "<table class='print-table'>"
                            html += "<tr><th>Athlete</th><th>Prior Best at Meet</th><th>1 Mile</th><th>2 Mile</th><th>Finish</th></tr>"

                            for uname in r_rows["Username"].tolist():
                                a_name = athlete_opts.get(uname, uname)
                                prior_time = ""
                                
                                prior_races = races_data[(races_data["Username"] == uname) & (races_data["Meet_Name"] == p_meet) & (races_data["Total_Time"].str.strip() != "")]
                                if not prior_races.empty:
                                    prior_races["Time_Sec"] = prior_races["Total_Time"].apply(time_to_seconds)
                                    prior_races = prior_races[prior_races["Time_Sec"] > 0]
                                    if not prior_races.empty:
                                        prior_time = seconds_to_time(prior_races["Time_Sec"].min())

                                if not prior_time:
                                    all_5k = races_data[(races_data["Username"] == uname) & (races_data["Distance"].str.upper() == "5K") & (races_data["Total_Time"].str.strip() != "")]
                                    if not all_5k.empty:
                                        all_5k["Time_Sec"] = all_5k["Total_Time"].apply(time_to_seconds)
                                        all_5k = all_5k[all_5k["Time_Sec"] > 0]
                                        if not all_5k.empty:
                                            prior_time = f"{seconds_to_time(all_5k['Time_Sec'].min())} (PR)"

                                html += f"<tr><td>{a_name}</td><td>{prior_time}</td><td></td><td></td><td></td></tr>"
                            html += "</table><br>"
                        st.markdown(html, unsafe_allow_html=True)

    # ----------------------------------
    # ATHLETE VIEW
    # ----------------------------------
    else:
        st.header("Training Dashboard")
        st.markdown("Your historical training and race data is below.")
        
        tab_dash, tab_rankings = st.tabs(["My Dashboard", "Team Rankings"])
        
        with tab_dash:
            u_races = races_data[races_data["Username"] == st.session_state["username"]]
            u_works = workouts_data[workouts_data["Username"] == st.session_state["username"]]
            
            athlete_seasons = sorted(list(set(u_races["Season"].tolist() + u_works["Season"].tolist())), reverse=True)
            if not athlete_seasons: athlete_seasons = [CURRENT_SEASON]
            
            sel_season = st.selectbox("View Season:", athlete_seasons, key="athlete_dash_season")
            st.markdown("---")
            
            user_races = u_races[(u_races["Active"].isin(["TRUE", "1", "1.0"])) & (u_races["Season"] == sel_season)].copy()
            user_workouts = u_works[u_works["Season"] == sel_season].copy()
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric(label=f"Races Completed ({sel_season})", value=len(user_races[user_races["Total_Time"].str.strip() != ""]))
            col_m2.metric(label=f"Workouts Logged ({sel_season})", value=len(user_workouts[user_workouts["Status"] == "Present"]))
            
            fastest_5k = "N/A"
            if not user_races.empty:
                five_k_races = user_races[user_races["Distance"].str.upper() == "5K"]
                if not five_k_races.empty:
                    fastest_sec = five_k_races["Total_Time"].apply(time_to_seconds).replace(0, float('inf')).min()
                    if fastest_sec != float('inf'): fastest_5k = seconds_to_time(fastest_sec)
                    
            col_m3.metric(label=f"5K PR ({sel_season})", value=fastest_5k)
            st.markdown("<br>", unsafe_allow_html=True)
            
            sub_races, sub_workouts = st.tabs(["Race Results", "Workouts"])
            with sub_races: display_athlete_races(st.session_state["username"], sel_season)
            with sub_workouts: display_athlete_workouts(st.session_state["username"], sel_season)
            
        with tab_rankings:
            show_rankings_tab()

if not st.session_state["logged_in"]: login_page()
elif st.session_state["first_login"]: password_reset_page()
else: home_page()
