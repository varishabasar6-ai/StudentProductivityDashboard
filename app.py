
import streamlit as st
import streamlit.components.v1 as components
import random
import time
import smtplib
from email.message import EmailMessage
import pandas as pd
import altair as alt
from datetime import date, datetime, timedelta, timezone
from supabase import create_client

# Intercept and fix the broken legacy cookie manager method
if not hasattr(st, "cache"):
    st.cache = st.cache_data

from streamlit_cookies_manager import EncryptedCookieManager


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Student Productivity Dashboard",
    page_icon="📚",
    layout="wide"
)


# ==================================================
# PROFESSIONAL PINK THEME
# ==================================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #fff8fb, #fff1f6);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

h1, h2, h3 {
    color: #713653 !important;
    font-weight: 650 !important;
}

.stMarkdown p,
.stCaption {
    color: #685564;
}

[data-testid="stSidebar"] {
    background: #fce8f1;
    border-right: 1px solid #f1d1e0;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #ead5e0;
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 3px 12px rgba(113, 54, 83, 0.06);
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {
    color: #654258 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div {
    color: #713653 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}

[data-testid="stForm"],
[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid #ead5e0;
    border-radius: 14px;
    padding: 14px;
}

.stApp,
.stApp p,
.stApp label {
    color: #443442;
}

.stButton > button,
.stFormSubmitButton > button {
    background: #b85c87;
    color: white;
    border: 1px solid #b85c87;
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #98446d;
    color: white;
    border-color: #98446d;
}

.stProgress > div > div > div > div {
    background: #c66b95;
}

hr {
    border-color: #efd5e1;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# SUPABASE & COOKIES
# ==================================================

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

cookies = EncryptedCookieManager(
    prefix="student_dashboard/",
    password=st.secrets["COOKIES_PASSWORD"]
)

if not cookies.ready():
    st.stop()

if "user" not in st.session_state:
    st.session_state.user = None

if "access_token" not in st.session_state:
    st.session_state.access_token = None


# ==================================================
# EMAIL NOTIFICATION FUNCTION
# ==================================================

def send_login_notification(login_email):
    try:
        message = EmailMessage()

        message["Subject"] = "Student Dashboard - New Login"
        message["From"] = st.secrets["EMAIL_ADDRESS"]
        message["To"] = st.secrets["NOTIFY_EMAIL"]

        message.set_content(
            f"A successful login occurred!\n"
            f"Account: {login_email}\n"
            f"Time: {datetime.now().astimezone().strftime('%d %b %Y, %I:%M %p')}"
        )

        with smtplib.SMTP_SSL(
            "smtp.gmail.com", 465, timeout=10
        ) as server:
            server.login(
                st.secrets["EMAIL_ADDRESS"],
                st.secrets["EMAIL_APP_PASSWORD"].replace(" ", "")
            )
            server.send_message(message)
            st.success("Email notification sent successfully!")

        return True

    except Exception as e:
        st.error(f"Email notification failed: {e}")
        return False


# ==================================================
# RESTORE LOGIN SESSION
# ==================================================

if (
    st.session_state.user is None
    and cookies.get("access_token")
    and cookies.get("refresh_token")
):
    try:
        response = supabase.auth.set_session(
            cookies.get("access_token"),
            cookies.get("refresh_token")
        )

        st.session_state.user = response.user
        st.session_state.access_token = (
            response.session.access_token
        )

        cookies["access_token"] = response.session.access_token
        cookies["refresh_token"] = response.session.refresh_token
        cookies.save()

    except Exception:
        cookies["access_token"] = ""
        cookies["refresh_token"] = ""
        cookies.save()


# ==================================================
# LOGIN / SIGN UP
# ==================================================

if st.session_state.user is None:

    st.title("Student Dashboard 🔐")
    st.write("Welcome back! Let's make today productive. 🌷")

    mode = st.radio(
        "Choose an option",
        ["Login", "Sign Up"]
    )

    with st.form("auth_form"):
        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        submit = st.form_submit_button(mode)

    if submit:
        if not email.strip() or not password:
            st.warning("Please enter your email and password.")

        else:
            try:
                if mode == "Sign Up":
                    response = supabase.auth.sign_up({
                        "email": email.strip(),
                        "password": password
                    })

                else:
                    response = supabase.auth.sign_in_with_password({
                        "email": email.strip(),
                        "password": password
                    })

                if response.session:

                    # Email notification only after successful login
                    if mode == "Login":
                        email_sent = send_login_notification(
                            email.strip()
                        )
                        st.write("DEBUG: Login notification function called")
                        st.write("DEBUG: Email sent =", email_sent)


                        if not email_sent:
                            st.warning(
                                "Login successful, but email notification "
                                "could not be sent. Check your email settings."
                            )

                    st.session_state.user = response.user

                    st.session_state.access_token = (
                        response.session.access_token
                    )

                    cookies["access_token"] = (
                        response.session.access_token
                    )

                    cookies["refresh_token"] = (
                        response.session.refresh_token
                    )

                    cookies.save()
                    st.rerun()

                else:
                    st.info(
                        "Check your email for confirmation, "
                        "then log in."
                    )

            except Exception:
                st.error(
                    "Login/signup failed. Check your details "
                    "and try again."
                )

    st.stop()


# ==================================================
# AUTHENTICATE DATABASE REQUESTS
# ==================================================

supabase.postgrest.auth(
    st.session_state.access_token
)


# ==================================================
# PAGE SETUP
# ==================================================

if "page" not in st.session_state:
    st.session_state.page = "Home"

st.title("📚 Student Productivity Dashboard")
st.write("Welcome! Let's make today productive. 💗")


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

st.sidebar.title("Navigation")

if st.sidebar.button("🏠 Home", use_container_width=True):
    st.session_state.page = "Home"
    st.rerun()

st.sidebar.caption("Your little steps matter 🌷💖")

if st.sidebar.button("📄 My Tasks", use_container_width=True):
    st.session_state.page = "My Tasks"
    st.rerun()

st.sidebar.caption("One task at a time 🎀✨")

if st.sidebar.button(
    "📊 Productivity Analysis",
    use_container_width=True
):
    st.session_state.page = "Productivity Analysis"
    st.rerun()

st.sidebar.caption("Look how far you've come 🌱💗")

if st.sidebar.button(
    "🌸 Your Relax Zone",
    use_container_width=True
):
    st.session_state.page = "Your Relax Zone"
    st.rerun()

st.sidebar.caption("Pause, breathe, reset 🌷🫧")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    cookies["access_token"] = ""
    cookies["refresh_token"] = ""
    cookies.save()

    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.page = "Home"

    st.rerun()

st.sidebar.caption("Rest well, come back stronger 🌙🩷")


# ==================================================
# HELPER FUNCTION
# ==================================================

def get_tasks():
    user_id = st.session_state.user.id

    response = (
        supabase.table("tasks")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    return response.data or []


# ==================================================
# SELECTED PAGE
# ==================================================

current_page = st.session_state.page
user_id = st.session_state.user.id


# ==================================================
# 1. HOME
# ==================================================

if current_page == "Home":

    st.subheader("Your Daily Overview 🌷")

    all_tasks = get_tasks()

    total_tasks = len(all_tasks)

    completed_tasks = sum(
        1 for task in all_tasks
        if task["is_completed"]
    )

    productivity = (
        round(completed_tasks / total_tasks * 100)
        if total_tasks > 0 else 0
    )

    today = date.today().isoformat()

    saved = (
        supabase.table("study_time")
        .select("hours")
        .eq("user_id", user_id)
        .eq("study_date", today)
        .execute()
    )

    default_hours = (
        float(saved.data[0]["hours"])
        if saved.data else 0.0
    )

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.metric("🗒 Total Tasks", total_tasks)

    with col2:
        with st.container(border=True):
            st.metric("✅ Completed Tasks", completed_tasks)

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.metric("⏰ Study Hours", default_hours)

    with col4:
        with st.container(border=True):
            st.metric("📊 Productivity", f"{productivity}%")

    st.divider()
    st.header("📚 Daily Study Tracker")

    study_hours = st.number_input(
        "How many hours did you study today?",
        min_value=0.0,
        max_value=24.0,
        value=default_hours,
        step=0.5,
        key="study_hours_input"
    )

    if st.button("💾 Save Study Hours"):
        try:
            supabase.table("study_time").upsert(
                {
                    "user_id": user_id,
                    "study_date": today,
                    "hours": study_hours
                },
                on_conflict="user_id,study_date"
            ).execute()

            st.success("Study hours saved successfully! 💗")
            st.rerun()

        except Exception as e:
            st.error(f"Could not save study hours: {e}")


# ==================================================
# 2. MY TASKS
# ==================================================

elif current_page == "My Tasks":

    st.header("✅ My Daily Tasks")
    st.caption("One task at a time 🎀")

    try:
        st.success("Supabase connected 💗")

        with st.expander("➕ Add a New Task"):

            task = st.text_input(
                "Enter a task",
                key="new_task"
            )

            if st.button("Add Task"):

                if task.strip():

                    supabase.table("tasks").insert({
                        "user_id": user_id,
                        "title": task.strip(),
                        "is_completed": False
                    }).execute()

                    st.success("Task saved successfully!")
                    st.rerun()

                else:
                    st.warning("Please enter a task first!")

        st.subheader("Your Task List")

        tasks = get_tasks()

        if not tasks:
            st.info("No tasks yet. Add your first task! 🌱")

        for task_item in tasks:

            task_col, delete_col = st.columns([4, 1])

            with task_col:
                completed = st.checkbox(
                    task_item["title"],
                    value=task_item["is_completed"],
                    key=f"task_{task_item['id']}"
                )

            with delete_col:
                delete_clicked = st.button(
                    "🗑️ Delete",
                    key=f"delete_{task_item['id']}"
                )

            if delete_clicked:

                supabase.table("tasks").delete().eq(
                    "id", task_item["id"]
                ).eq(
                    "user_id", user_id
                ).execute()

                st.rerun()

            if completed != task_item["is_completed"]:

                update_data = {
                    "is_completed": completed,
                    "completed_at": (
                        datetime.now(timezone.utc).isoformat()
                        if completed else None
                    )
                }

                supabase.table("tasks").update(
                    update_data
                ).eq(
                    "id", task_item["id"]
                ).eq(
                    "user_id", user_id
                ).execute()

                st.rerun()

            if task_item["is_completed"]:
                st.success("✅ Completed!")
            else:
                st.caption("⌛ Pending")

    except Exception as e:
        st.error(f"Could not load tasks: {e}")


# ==================================================
# 3. PRODUCTIVITY ANALYSIS
# ==================================================

elif current_page == "Productivity Analysis":

    st.header("📊 Productivity Analysis")
    st.caption("Your progress, saved and tracked over time ✨")

    try:
        analysis_tasks = (
            supabase.table("tasks")
            .select("id, title, is_completed, completed_at")
            .eq("user_id", user_id)
            .execute()
        ).data or []

        total = len(analysis_tasks)

        done = sum(
            1 for task in analysis_tasks
            if task["is_completed"]
        )

        pending = total - done

        percentage = (
            round(done / total * 100)
            if total else 0
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("📝 Total Tasks", total)
        c2.metric("✅ Completed", done)
        c3.metric("⏳ Pending", pending)

        st.progress(percentage / 100)

        st.write(
            f"✨ **{percentage}%** of your tasks completed!"
        )

        # ---------- DAILY TASK PROGRESS GRAPH ----------

        st.subheader("🌷 Daily Task Progress")

        completed_records = [
            task for task in analysis_tasks
            if task["is_completed"] and task.get("completed_at")
        ]

        today_date = date.today()

        dates = [
            today_date - timedelta(days=i)
            for i in range(6, -1, -1)
        ]

        daily_counts = {day: 0 for day in dates}

        for task in completed_records:

            completed_date = (
                pd.to_datetime(task["completed_at"], utc=True)
                .tz_convert("Asia/Kolkata")
                .date()
            )

            if completed_date in daily_counts:
                daily_counts[completed_date] += 1

        chart_data = pd.DataFrame({
            "Date": [day.strftime("%d %b") for day in dates],
            "Tasks Completed": list(daily_counts.values())
        })

        task_chart = alt.Chart(chart_data).mark_bar(
            color="#C66B95",
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5
        ).encode(
            x=alt.X(
                "Date:N",
                sort=None,
                axis=alt.Axis(
                    title=None,
                    labelColor="#654258",
                    domainColor="#EAD5E0",
                    tickColor="#EAD5E0",
                    grid=False,
                    labelAngle=0
                )
            ),
            y=alt.Y(
                "Tasks Completed:Q",
                axis=alt.Axis(
                    title="Tasks Completed",
                    titleColor="#654258",
                    labelColor="#654258",
                    gridColor="#F0DCE6",
                    domainColor="#EAD5E0",
                    tickColor="#EAD5E0",
                    tickMinStep=1
                )
            ),
            tooltip=["Date", "Tasks Completed"]
        ).properties(
            background="#FFFFFF",
            height=280
        )

        st.altair_chart(
            task_chart,
            use_container_width=True
        )

        if not completed_records:
            st.info(
                "Complete a task to start building your "
                "daily progress graph! 🌱"
            )

        # ---------- DAILY STUDY HOURS GRAPH ----------

        st.subheader("📚 Daily Study Hours")

        study_records = (
            supabase.table("study_time")
            .select("study_date, hours")
            .eq("user_id", user_id)
            .gte(
                "study_date",
                (today_date - timedelta(days=6)).isoformat()
            )
            .lte(
                "study_date",
                today_date.isoformat()
            )
            .execute()
        ).data or []

        if study_records:

            hours_data = pd.DataFrame(study_records)

            hours_data["Date"] = pd.to_datetime(
                hours_data["study_date"]
            ).dt.strftime("%d %b")

            hours_data = hours_data[["Date", "hours"]].rename(
                columns={"hours": "Study Hours"}
            )

            hours_chart = alt.Chart(hours_data).mark_bar(
                color="#C66B95",
                cornerRadiusTopLeft=5,
                cornerRadiusTopRight=5
            ).encode(
                x=alt.X(
                    "Date:N",
                    sort=None,
                    axis=alt.Axis(
                        title=None,
                        labelColor="#654258",
                        domainColor="#EAD5E0",
                        tickColor="#EAD5E0",
                        grid=False,
                        labelAngle=0
                    )
                ),
                y=alt.Y(
                    "Study Hours:Q",
                    axis=alt.Axis(
                        title="Study Hours",
                        titleColor="#654258",
                        labelColor="#654258",
                        gridColor="#F0DCE6",
                        domainColor="#EAD5E0",
                        tickColor="#EAD5E0"
                    )
                ),
                tooltip=["Date", "Study Hours"]
            ).properties(
                background="#FFFFFF",
                height=280
            )

            st.altair_chart(
                hours_chart,
                use_container_width=True
            )

        else:
            st.info(
                "Save your study hours each day to see "
                "your study trend here! 📖"
            )

        st.caption(
            "Your analysis uses your saved Supabase data. "
            "Keep going, one task at a time! 💗"
        )

    except Exception as e:
        st.error(f"Could not load analysis: {e}")


# ==================================================
# 4. YOUR RELAX ZONE
# ==================================================

elif current_page == "Your Relax Zone":

    st.header("🌸 Your Relax Zone")

    st.subheader("🌬️ Breathe In")

    st.write(
        "Take a moment for yourself. "
        "Breathe slowly and relax."
    )

    components.html("""
    <div style="text-align:center; padding:20px;">
      <style>
        .breathing-circle {
          width:140px;
          height:140px;
          margin:auto;
          border-radius:50%;
          background:radial-gradient(circle,#ffd6e7,#f48fb1);
          box-shadow:0 0 30px #f8bbd0;
          animation:breathe 8s ease-in-out infinite;
          display:flex;
          align-items:center;
          justify-content:center;
          color:#7a2848;
          font-size:18px;
          font-weight:bold;
        }

        @keyframes breathe {
          0%,100% { transform:scale(0.75); }
          50% { transform:scale(1.15); }
        }
      </style>

      <div class="breathing-circle">Breathe In 💗</div>
      <p style="color:#c46a91;">Slow in... slow out...</p>
    </div>
    """, height=230)

    st.divider()

    # ---------- MEMORY MATCH GAME ----------

    st.subheader("🃏 Memory Match")
    st.write("Flip the cards and find matching pairs! 💗")

    if "memory_cards" not in st.session_state:

        symbols = ["🐱", "🐻", "🐸", "🦋"]

        st.session_state.memory_cards = symbols * 2

        random.shuffle(st.session_state.memory_cards)

        st.session_state.flipped_cards = []
        st.session_state.matched_cards = []

    if st.button("🔄 Restart Game"):

        symbols = ["🐱", "🐻", "🐸", "🦋"]

        st.session_state.memory_cards = symbols * 2

        random.shuffle(st.session_state.memory_cards)

        st.session_state.flipped_cards = []
        st.session_state.matched_cards = []

        st.session_state.pop("match_message", None)

        st.rerun()

    card_cols = st.columns(4)

    for i, symbol in enumerate(st.session_state.memory_cards):

        with card_cols[i % 4]:

            if i in st.session_state.matched_cards:
                st.success(symbol)

            elif i in st.session_state.flipped_cards:
                st.info(symbol)

            elif len(st.session_state.flipped_cards) < 2:

                if st.button("💗", key=f"memory_{i}"):

                    st.session_state.flipped_cards.append(i)
                    st.rerun()

            else:
                st.button(
                    "💗",
                    key=f"memory_{i}",
                    disabled=True
                )

    if len(st.session_state.flipped_cards) == 2:

        first, second = st.session_state.flipped_cards

        if (
            st.session_state.memory_cards[first]
            == st.session_state.memory_cards[second]
        ):

            st.session_state.matched_cards.extend(
                [first, second]
            )

            st.session_state.flipped_cards = []

            st.session_state.match_message = (
                "✨ Yayyy! Perfect match! 💖"
            )

            st.toast("✨ Perfect match! 🎉")
            st.rerun()

        else:

            st.session_state.match_message = (
                "🥺 Oops! Try again!"
            )

            st.warning("🥺 Not a match! Try again...")

            time.sleep(1.2)

            st.session_state.flipped_cards = []
            st.rerun()

    if "match_message" in st.session_state:
        st.info(st.session_state.match_message)

    if len(st.session_state.matched_cards) == 8:
        st.balloons()
        st.success("Yay! You matched every pair! 🎉💗")

    # ---------- SECRET SURPRISE ----------

    st.divider()

    st.markdown("""
    <style>
    .secret-heading {
        text-align:center;
        color:#B83270;
        font-size:30px;
    }

    div.stButton > button {
        background-color:#FCE4EF;
        color:#B83270;
        border:2px solid #E9A2C3;
        border-radius:16px;
        font-weight:bold;
        padding:12px;
    }

    div.stButton > button:hover {
        background-color:#F8D0E3;
        color:#A52A63;
        border-color:#D879A7;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        "<h2 class='secret-heading'>💌 A Little Surprise</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;color:#A64D79;'>"
        "A tiny surprise is waiting for you... 🎀"
        "</p>",
        unsafe_allow_html=True
    )

    if st.button(
        "💗 Tap to Open 💗",
        key="secret_surprise",
        use_container_width=True
    ):
        st.session_state.show_surprise = True

    if st.session_state.get("show_surprise", False):

        components.html("""
        <div style="background:#FFF0F6;padding:25px;
                    border-radius:24px;text-align:center;
                    color:#B83270;font-family:Arial;">

            <div style="font-size:80px;">🐰🎀</div>

            <h2>Thank You for Being Here! 💗</h2>

            <p>
                I hope this little space brings you happiness,
                peaceful moments, and lots of smiles. 🌷
            </p>

            <h3>Sending you lots of love 💕</h3>

            <p>♡ Designed with love by Varisha ♡</p>

        </div>
        """, height=350)
