import streamlit as st
import streamlit.components.v1 as components
from streamlit_geolocation import streamlit_geolocation
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import joblib
import pandas as pd
import random
import base64
import os
import textwrap

# =========================================================
# LAST SIGNAL
# Machine Learning-Based Personal Safety System
# =========================================================

st.set_page_config(
    page_title="Last Signal",
    page_icon="🐰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BUNNY_PATH = os.path.join(BASE_DIR, "bunny.gif")
WALLPAPER_PATH = os.path.join(BASE_DIR, "wallpaper.jpeg")
DATABASE_PATH = os.path.join(BASE_DIR, "lastsignal.db")
MODEL_PATH = os.path.join(BASE_DIR, "last_signal_model.pkl")

# =========================================================
# SESSION STATE
# =========================================================

if "started" not in st.session_state:
    st.session_state.started = False

if "safety_active" not in st.session_state:
    st.session_state.safety_active = False

if "signal_lost" not in st.session_state:
    st.session_state.signal_lost = False

if "session_end" not in st.session_state:
    st.session_state.session_end = None

if "last_risk" not in st.session_state:
    st.session_state.last_risk = 0

if "last_prediction" not in st.session_state:
    st.session_state.last_prediction = "Safe"

if "emergency_queued" not in st.session_state:
    st.session_state.emergency_queued = False

if "emergency_message" not in st.session_state:
    st.session_state.emergency_message = ""

# =========================================================
# LOAD FILES
# =========================================================

wallpaper_base64 = ""

if os.path.exists(WALLPAPER_PATH):
    with open(WALLPAPER_PATH, "rb") as f:
        wallpaper_base64 = base64.b64encode(
            f.read()
        ).decode("utf-8")

bunny_base64 = ""

if os.path.exists(BUNNY_PATH):
    with open(BUNNY_PATH, "rb") as f:
        bunny_base64 = base64.b64encode(
            f.read()
        ).decode("utf-8")

# =========================================================
# GLOBAL DESIGN
# =========================================================

if wallpaper_base64:
    background = f"""
    .stApp {{
        background-image:
            linear-gradient(
                rgba(255, 228, 238, 0.18),
                rgba(255, 228, 238, 0.18)
            ),
            url("data:image/jpeg;base64,{wallpaper_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        min-height: 100vh;
    }}
    """
else:
    background = """
    .stApp {
        background: linear-gradient(
            135deg,
            #ffdfe9,
            #fff7fa
        );
    }
    """

st.markdown(textwrap.dedent(f"""<style>
{background}
#MainMenu {{
    visibility: hidden;
}}
footer {{
    visibility: hidden;
}}
header {{
    background: transparent !important;
}}
.block-container {{
    max-width: 900px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}}
html, body, [class*="css"] {{
    font-family: Arial, sans-serif;
    color: #3b3039 !important;
}}
/* Mobile readability */
.stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li,
[data-testid="stTextInput"] label, [data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label, [data-testid="stSelectbox"] label,
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label,
[data-testid="stFileUploader"] label, .stCaption,
[data-testid="stWidgetLabel"] {{
    color: #3b3039 !important;
}}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {{
    color: #2f2630 !important;
    -webkit-text-fill-color: #2f2630 !important;
    background: rgba(255,255,255,0.92) !important;
}}
.stLinkButton a, .stLinkButton a:visited {{
    color: #3b3039 !important;
}}
/* Keep emergency panel text white */
.emergency, .emergency * {{
    color: #ffffff !important;
}}
@media (max-width: 640px) {{
    .block-container {{
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }}
    .big-title {{ font-size: 28px; }}
    .section {{ font-size: 18px; }}
    .stButton > button, .stLinkButton > a {{
        min-height: 52px !important;
        font-size: 15px !important;
    }}
}}
/* Main glass containers */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(18px);
    border-radius: 26px;
    border: 1px solid rgba(255,255,255,0.85);
}}
/* Buttons */
.stButton > button {{
    border-radius: 16px !important;
    min-height: 50px !important;
    font-weight: 700 !important;
    border: 0 !important;
    box-shadow: 0 8px 22px rgba(70,40,70,0.10);
    transition: 0.2s ease;
}}
.stButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 28px rgba(70,40,70,0.16);
}}
.stLinkButton > a {{
    border-radius: 16px !important;
    font-weight: 700 !important;
}}
/* Titles */
.big-title {{
    text-align: center;
    color: #3b3039;
    font-size: 34px;
    font-weight: 800;
}}
.sub-title {{
    text-align: center;
    color: #776b78;
}}
.section {{
    color: #403642;
    font-size: 21px;
    font-weight: 800;
    margin-top: 25px;
    margin-bottom: 10px;
}}
/* Mini cards */
.mini {{
    background: rgba(255,255,255,0.78);
    border: 1px solid rgba(255,255,255,0.9);
    border-radius: 20px;
    padding: 16px 5px;
    text-align: center;
    box-shadow: 0 8px 20px rgba(70,40,70,0.07);
}}
.mini-icon {{
    font-size: 27px;
}}
.mini-value {{
    font-weight: 800;
    color: #403642;
}}
.mini-label {{
    font-size: 9px;
    letter-spacing: 1px;
    color: #8a7d8b;
}}
/* Emergency */
.emergency {{
    background: linear-gradient(
        135deg,
        #5d0712,
        #b5122e
    );
    color: white;
    border-radius: 30px;
    padding: 42px 20px;
    text-align: center;
    box-shadow: 0 15px 60px rgba(170,0,25,0.45);
}}
.emergency h1 {{
    font-size: 38px;
    margin: 8px 0;
}}
.emergency-icon {{
    font-size: 68px;
}}
/* Safe */
.safe {{
    background: linear-gradient(
        135deg,
        rgba(236,253,245,0.95),
        rgba(240,253,244,0.95)
    );
    border: 1px solid #bbf7d0;
    border-radius: 30px;
    padding: 32px;
    text-align: center;
    box-shadow: 0 12px 35px rgba(34,197,94,0.10);
}}
.safe-icon {{
    font-size: 60px;
}}
.safe-title {{
    font-size: 29px;
    font-weight: 800;
    color: #166534;
}}
/* Footer */
.footer {{
    text-align: center;
    color: #8a7d8b;
    font-size: 12px;
    margin-top: 35px;
}}
</style>"""), unsafe_allow_html=True)

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect(DATABASE_PATH)

cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS safety_profile (
        id INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT,
        emergency_name TEXT,
        emergency_phone TEXT
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS heartbeat (
        id INTEGER PRIMARY KEY,
        last_seen TEXT
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS emergency_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        emergency_phone TEXT,
        message TEXT,
        status TEXT
    )
    """
)

conn.commit()

cursor.execute(
    "SELECT * FROM safety_profile LIMIT 1"
)

profile = cursor.fetchone()

# =========================================================
# ML MODEL
# =========================================================

try:
    ml_model = joblib.load(MODEL_PATH)
    model_loaded = True
except Exception:
    ml_model = None
    model_loaded = False

# =========================================================
# FULL RESET: Z → A
# =========================================================

def full_reset():
    """Clear the complete demo state and return to the bunny opening."""
    reset_conn = sqlite3.connect(DATABASE_PATH)
    reset_cursor = reset_conn.cursor()
    reset_cursor.execute("DELETE FROM safety_profile")
    reset_cursor.execute("DELETE FROM heartbeat")
    reset_cursor.execute("DELETE FROM emergency_queue")
    reset_conn.commit()
    reset_conn.close()

    for key in [
        "started",
        "safety_active",
        "signal_lost",
        "session_end",
        "last_risk",
        "last_prediction",
        "emergency_queued",
        "emergency_message",
    ]:
        if key in st.session_state:
            del st.session_state[key]

# =========================================================
# CINEMATIC WELCOME SCREEN
# =========================================================

if not st.session_state.started:

    if bunny_base64:

        components.html(
            f"""
<!DOCTYPE html>
<html>
<head>
<style>

html, body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: transparent;
    overflow: hidden;
}}

.scene {{
    height: 720px;
    width: 100%;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
}}

.spark {{
    position: absolute;
    color: white;
    font-size: 30px;
    animation: twinkle 2.8s ease-in-out infinite;
}}

.s1 {{ top: 12%; left: 12%; }}
.s2 {{ top: 20%; right: 14%; animation-delay: .7s; }}
.s3 {{ bottom: 20%; left: 15%; animation-delay: 1.4s; }}
.s4 {{ bottom: 13%; right: 12%; animation-delay: 2s; }}

@keyframes twinkle {{
    0%, 100% {{
        opacity: .25;
        transform: scale(.7);
    }}
    50% {{
        opacity: 1;
        transform: scale(1.5);
    }}
}}

.bunny {{
    width: 570px;
    max-width: 88vw;
    max-height: 550px;
    object-fit: contain;
    border-radius: 45px;
    animation: appear 1.2s ease;
}}

@keyframes appear {{
    from {{
        opacity: 0;
        transform: scale(.72);
    }}
    to {{
        opacity: 1;
        transform: scale(1);
    }}
}}

.question {{
    margin-top: 8px;
    font-family: Arial, sans-serif;
    font-size: 48px;
    font-weight: 800;
    color: #3b3039;
}}

.subtitle {{
    margin-top: 8px;
    font-family: Arial, sans-serif;
    font-size: 18px;
    color: #766776;
}}

.brand {{
    margin-top: 18px;
    font-family: Arial, sans-serif;
    font-size: 12px;
    letter-spacing: 5px;
    color: #a08096;
}}

</style>
</head>

<body>

<div class="scene">

    <div class="spark s1">✦</div>
    <div class="spark s2">✧</div>
    <div class="spark s3">✦</div>
    <div class="spark s4">✧</div>

    <img
        class="bunny"
        src="data:image/gif;base64,{bunny_base64}"
    >

    <div class="question">
        u okay?
    </div>

    <div class="subtitle">
        I'm here with you. 💗
    </div>

    <div class="brand">
        LAST SIGNAL
    </div>

</div>

</body>
</html>
""",
            height=730,
            scrolling=False
        )

    else:

        st.markdown(textwrap.dedent("""            <div style="
                text-align:center;
                font-size:170px;
                padding-top:120px;
            ">
                🐰
            </div>"""), unsafe_allow_html=True)

        st.markdown(
            '<div class="big-title">u okay?</div>',
            unsafe_allow_html=True
        )

    if st.button(
        "💗  I'm okay — Let's start",
        use_container_width=True
    ):
        st.session_state.started = True
        st.rerun()

    st.stop()

# =========================================================
# HEADER
# =========================================================

st.markdown(textwrap.dedent("""    <div class="big-title">
        🛡️ Last Signal
    </div>
    <div class="sub-title">
        Intelligent Personal Safety & Emergency Response
    </div>"""), unsafe_allow_html=True)

st.write("")

# A visible reset button makes the Z → A flow obvious during the demo.
logout_col1, logout_col2 = st.columns([3, 2])
with logout_col2:
    if st.button("🚪 Logout & Start Again", use_container_width=True, key="top_logout"):
        full_reset()
        st.rerun()

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## ⚙️ Settings")

    st.caption(
        "Restart the project demonstration from the beginning."
    )

    if st.button(
        "🚪 Logout & Start Again",
        use_container_width=True
    ):
        full_reset()
        st.rerun()

# =========================================================
# LOCATION
# =========================================================

# Browser GPS requires the user to grant location permission.
# The dedicated Streamlit geolocation component is more reliable for
# a deployed Streamlit app than evaluating geolocation JavaScript directly.
if "latitude" not in st.session_state:
    st.session_state.latitude = None
if "longitude" not in st.session_state:
    st.session_state.longitude = None

location = streamlit_geolocation()

if isinstance(location, dict):
    lat = location.get("latitude")
    lon = location.get("longitude")
    if lat is not None and lon is not None:
        st.session_state.latitude = lat
        st.session_state.longitude = lon

latitude = st.session_state.latitude
longitude = st.session_state.longitude

# =========================================================
# FIRST-TIME SETUP
# =========================================================

if profile is None:

    st.markdown(textwrap.dedent("""        <div class="big-title">
            💗
        </div>
        <div class="big-title">
            Let's get you set up
        </div>
        <div class="sub-title">
            Just four details. Nothing complicated.
        </div>"""), unsafe_allow_html=True)

    st.write("")

    with st.form("safety_setup"):

        name = st.text_input(
            "👤 Your name"
        )

        phone = st.text_input(
            "📱 Your phone number"
        )

        emergency_name = st.text_input(
            "🚨 Emergency contact name"
        )

        emergency_phone = st.text_input(
            "📞 Emergency contact number"
        )

        submitted = st.form_submit_button(
            "💗 Save & Continue",
            use_container_width=True
        )

        if submitted:

            if not name:
                st.error(
                    "Please enter your name."
                )

            elif not phone:
                st.error(
                    "Please enter your phone number."
                )

            elif not emergency_name:
                st.error(
                    "Please enter an emergency contact."
                )

            elif not emergency_phone:
                st.error(
                    "Please enter the emergency contact number."
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO safety_profile
                    (
                        id,
                        name,
                        phone,
                        emergency_name,
                        emergency_phone
                    )
                    VALUES
                    (1, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        phone,
                        emergency_name,
                        emergency_phone
                    )
                )

                conn.commit()

                st.success(
                    "Safety profile saved. 💗"
                )

                st.rerun()

    st.stop()

# =========================================================
# LOCATION STATUS
# =========================================================

if profile is not None:
    st.markdown(
        '<div class="section">📍 Your Current Location</div>',
        unsafe_allow_html=True
    )

    if latitude is not None and longitude is not None:
        st.success(f"📍 Location secured: {latitude:.6f}, {longitude:.6f}")
        maps_url = (
            "https://www.google.com/maps/search/?api=1"
            f"&query={latitude},{longitude}"
        )
        st.link_button("🗺️ VIEW MY LOCATION", maps_url, use_container_width=True)
    else:
        st.warning("Location not captured yet. Tap the location button above and allow browser location permission.")

# =========================================================
# HOME
# =========================================================

if not st.session_state.safety_active:

    st.markdown(textwrap.dedent(f"""        <div class="safe">
            <div class="safe-icon">
                🐰
            </div>
            <div class="safe-title">
                Hi {profile[1]} 💗
            </div>
            <p>
                You're safe here.
            </p>
        </div>"""), unsafe_allow_html=True)

    st.markdown(
        '<div class="section">🛡️ Start Safety Mode</div>',
        unsafe_allow_html=True
    )

    st.info(
        "Last Signal will monitor the safety signals "
        "during your selected session."
    )

    duration = st.selectbox(
        "Safety session",
        [
            "30 minutes",
            "1 hour",
            "2 hours",
            "4 hours"
        ]
    )

    if st.button(
        "🟢 START SAFETY MODE",
        use_container_width=True
    ):

        minutes = {
            "30 minutes": 30,
            "1 hour": 60,
            "2 hours": 120,
            "4 hours": 240
        }[duration]

        st.session_state.safety_active = True

        st.session_state.session_end = (
            datetime.now()
            + timedelta(
                minutes=minutes
            )
        )

        st.session_state.signal_lost = False

        st.rerun()

    st.markdown(
        '<div class="section">✨ System Ready</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(textwrap.dedent("""            <div class="mini">
                <div class="mini-icon">📍</div>
                <div class="mini-value">GPS</div>
                <div class="mini-label">LOCATION</div>
            </div>"""), unsafe_allow_html=True)

    with c2:
        st.markdown(textwrap.dedent("""            <div class="mini">
                <div class="mini-icon">🧠</div>
                <div class="mini-value">READY</div>
                <div class="mini-label">AI MODEL</div>
            </div>"""), unsafe_allow_html=True)

    with c3:
        st.markdown(textwrap.dedent("""            <div class="mini">
                <div class="mini-icon">❤️</div>
                <div class="mini-value">ACTIVE</div>
                <div class="mini-label">SIGNAL</div>
            </div>"""), unsafe_allow_html=True)

# =========================================================
# ACTIVE SAFETY MODE
# =========================================================

else:

    # =====================================================
    # SIMULATED SENSOR SIGNALS
    # =====================================================

    if st.session_state.signal_lost:

        heart_rate = 125
        movement = 0.5
        battery = 8
        signal_strength = 15
        time_since_heartbeat = 55
        location_change = 0
        check_in_overdue = 1

    else:

        heart_rate = random.randint(
            65,
            90
        )

        movement = round(
            random.uniform(
                3,
                8
            ),
            1
        )

        battery = random.randint(
            50,
            95
        )

        signal_strength = random.randint(
            70,
            100
        )

        time_since_heartbeat = random.randint(
            5,
            15
        )

        location_change = round(
            random.uniform(
                0.5,
                3
            ),
            1
        )

        check_in_overdue = 0

    # =====================================================
    # ML PREDICTION
    # =====================================================

    if model_loaded:

        input_data = pd.DataFrame(
            [[
                heart_rate,
                movement,
                battery,
                signal_strength,
                time_since_heartbeat,
                location_change,
                check_in_overdue
            ]],
            columns=[
                "heart_rate",
                "movement",
                "battery",
                "signal_strength",
                "time_since_heartbeat",
                "location_change",
                "check_in_overdue"
            ]
        )

        prediction = ml_model.predict(
            input_data
        )[0]

        probabilities = (
            ml_model.predict_proba(
                input_data
            )[0]
        )

        classes = ml_model.classes_

        probability_dict = dict(
            zip(
                classes,
                probabilities
            )
        )

        risk_weights = {
            "Safe": 0,
            "Caution": 33,
            "High Risk": 66,
            "Emergency": 100
        }

        risk_score = sum(
            probability_dict.get(
                level,
                0
            ) * weight
            for level, weight in risk_weights.items()
        )

        risk_score = round(
            risk_score,
            1
        )

        st.session_state.last_risk = risk_score

        st.session_state.last_prediction = prediction

    else:

        prediction = "Safe"
        risk_score = 0

    # =====================================================
    # EMERGENCY
    # =====================================================

    if st.session_state.signal_lost:

        # The model has received the emergency-pattern signals.
        # Queue the SMS locally so the prototype never falsely claims
        # that a browser can silently send an SMS.
        emergency_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        location_text = (
            f"{latitude}, {longitude}"
            if latitude is not None and longitude is not None
            else "Last known location unavailable"
        )
        emergency_message = (
            f"LAST SIGNAL EMERGENCY ALERT\n\n"
            f"{profile[1]} may be in danger.\n"
            f"AI status: Emergency\n"
            f"Risk score: {st.session_state.last_risk}%\n"
            f"Time: {emergency_time}\n"
            f"Last location: {location_text}\n\n"
            f"Please contact them immediately.\n"
            f"This alert was prepared by Last Signal."
        )
        st.session_state.emergency_message = emergency_message

        if not st.session_state.emergency_queued:
            queue_conn = sqlite3.connect(DATABASE_PATH)
            queue_cursor = queue_conn.cursor()
            queue_cursor.execute(
                "INSERT INTO emergency_queue (created_at, emergency_phone, message, status) VALUES (?, ?, ?, ?)",
                (emergency_time, str(profile[4]), emergency_message, "QUEUED — waiting for cellular delivery")
            )
            queue_conn.commit()
            queue_conn.close()
            st.session_state.emergency_queued = True

        st.markdown(textwrap.dedent("""            <div class="emergency">
                <div class="emergency-icon">
                    🚨
                </div>
                <h1>
                    LAST SIGNAL LOST
                </h1>
                <div>
                    AI detected an emergency condition.
                </div>
                <br>
                <div>
                    Your last known information
                    has been secured.
                </div>
            </div>"""), unsafe_allow_html=True)

        st.markdown(
            '<div class="section">📍 Last Known Location</div>',
            unsafe_allow_html=True
        )

        if (
            latitude is not None
            and longitude is not None
        ):

            st.success(
                "Location secured"
            )

            st.write(
                f"Latitude: {latitude}"
            )

            st.write(
                f"Longitude: {longitude}"
            )

            maps_url = (
                "https://www.google.com/maps/search/"
                "?api=1"
                f"&query={latitude},{longitude}"
            )

            st.link_button(
                "🗺️ OPEN LAST LOCATION",
                maps_url,
                use_container_width=True
            )

        else:

            st.warning(
                "Location unavailable."
            )

        st.markdown(
            '<div class="section">📨 Emergency SMS</div>',
            unsafe_allow_html=True
        )

        st.success("SMS READY — emergency message has been prepared and queued.")
        st.caption(
            "Prototype note: a browser cannot silently send SMS. "
            "The Android production version can send the queued message through the phone's cellular network when service is available."
        )

        sms_body = urllib.parse.quote(st.session_state.emergency_message)
        sms_recipient = urllib.parse.quote(str(profile[4]).strip())
        sms_url = f"sms:{sms_recipient}?body={sms_body}"

        st.link_button(
            "📱 OPEN SMS WITH ALERT",
            sms_url,
            use_container_width=True
        )

        st.code(st.session_state.emergency_message, language=None)

        st.download_button(
            "📨 SAVE QUEUED SMS",
            st.session_state.emergency_message,
            file_name="Last_Signal_Emergency_SMS.txt",
            mime="text/plain",
            use_container_width=True
        )

        st.markdown(
            '<div class="section">🚨 Emergency Contact</div>',
            unsafe_allow_html=True
        )

        st.success(
            f"Emergency contact: {profile[3]}"
        )

        emergency_phone = str(
            profile[4]
        ).strip()

        call_url = (
            "tel:"
            + urllib.parse.quote(
                emergency_phone
            )
        )

        st.link_button(
            "📞 CONTACT EMERGENCY PERSON",
            call_url,
            use_container_width=True
        )

        emergency_report = f"""
LAST SIGNAL EMERGENCY REPORT

User:
{profile[1]}

Phone:
{profile[2]}

Emergency Contact:
{profile[3]}

Emergency Phone:
{profile[4]}

AI Risk Score:
{st.session_state.last_risk}%

AI Prediction:
{st.session_state.last_prediction}

Last Known Location:
{location_text}

Time:
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Status:
Emergency condition detected.

SMS Status:
Queued — waiting for cellular delivery.
"""

        st.download_button(
            "📥 SAVE EMERGENCY REPORT",
            emergency_report,
            file_name="Last_Signal_Emergency_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

        if st.button(
            "💗 I'M SAFE NOW",
            use_container_width=True
        ):

            st.session_state.signal_lost = False
            st.session_state.safety_active = False
            st.session_state.session_end = None
            st.session_state.emergency_queued = False
            st.session_state.emergency_message = ""

            queue_conn = sqlite3.connect(DATABASE_PATH)
            queue_conn.execute("DELETE FROM emergency_queue")
            queue_conn.commit()
            queue_conn.close()

            st.rerun()

    # =====================================================
    # NORMAL SAFETY MODE
    # =====================================================

    else:

        st.markdown(textwrap.dedent("""            <div class="safe">
                <div class="safe-icon">
                    🛡️
                </div>
                <div class="safe-title">
                    YOU'RE PROTECTED
                </div>
                <p>
                    Last Signal is watching over you. 💗
                </p>
            </div>"""), unsafe_allow_html=True)

        if st.session_state.session_end:

            st.info(
                "⏱️ Safety Mode active until "
                f"**{st.session_state.session_end.strftime('%I:%M %p')}**"
            )

        # -------------------------------------------------
        # AI
        # -------------------------------------------------

        st.markdown(
            '<div class="section">🧠 AI Safety Intelligence</div>',
            unsafe_allow_html=True
        )

        if prediction == "Safe":

            status = "🟢 SAFE"

            message = (
                "No significant risk detected."
            )

        elif prediction == "Caution":

            status = "🟡 CAUTION"

            message = (
                "Something looks unusual."
            )

        elif prediction == "High Risk":

            status = "🟠 HIGH RISK"

            message = (
                "Higher risk detected."
            )

        else:

            status = "🔴 EMERGENCY"

            message = (
                "Emergency risk detected."
            )

        st.metric(
            "Machine Learning Safety Status",
            status,
            f"Risk {risk_score}%"
        )

        st.caption(
            message
        )

        st.progress(
            min(
                int(risk_score),
                100
            )
        )

        # -------------------------------------------------
        # SIGNALS
        # -------------------------------------------------

        st.markdown(
            '<div class="section">📡 Live Safety Signals</div>',
            unsafe_allow_html=True
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.markdown(textwrap.dedent(f"""                <div class="mini">
                    <div class="mini-icon">❤️</div>
                    <div class="mini-value">{heart_rate}</div>
                    <div class="mini-label">HEART RATE</div>
                </div>"""), unsafe_allow_html=True)

        with c2:

            st.markdown(textwrap.dedent(f"""                <div class="mini">
                    <div class="mini-icon">📶</div>
                    <div class="mini-value">{signal_strength}%</div>
                    <div class="mini-label">SIGNAL</div>
                </div>"""), unsafe_allow_html=True)

        with c3:

            st.markdown(textwrap.dedent(f"""                <div class="mini">
                    <div class="mini-icon">🔋</div>
                    <div class="mini-value">{battery}%</div>
                    <div class="mini-label">BATTERY</div>
                </div>"""), unsafe_allow_html=True)

        with c4:

            location_status = (
                "LIVE"
                if (
                    latitude is not None
                    and longitude is not None
                )
                else "WAITING"
            )

            st.markdown(textwrap.dedent(f"""                <div class="mini">
                    <div class="mini-icon">📍</div>
                    <div class="mini-value">{location_status}</div>
                    <div class="mini-label">LOCATION</div>
                </div>"""), unsafe_allow_html=True)

        # -------------------------------------------------
        # HEARTBEAT
        # -------------------------------------------------

        now = datetime.now()

        heartbeat_conn = sqlite3.connect(
            DATABASE_PATH
        )

        heartbeat_cursor = (
            heartbeat_conn.cursor()
        )

        heartbeat_cursor.execute(
            """
            INSERT OR REPLACE INTO heartbeat
            (id, last_seen)
            VALUES (1, ?)
            """,
            (
                now.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )
        )

        heartbeat_conn.commit()

        heartbeat_conn.close()

        st.caption(
            "❤️ Last signal • "
            + now.strftime(
                "%I:%M:%S %p"
            )
        )

        # -------------------------------------------------
        # I'M SAFE
        # -------------------------------------------------

        if st.button(
            "💗 I'M SAFE",
            use_container_width=True
        ):

            st.session_state.safety_active = False
            st.session_state.session_end = None
            st.session_state.signal_lost = False

            st.rerun()

        # -------------------------------------------------
        # DEMO
        # -------------------------------------------------

        st.markdown("---")

        with st.expander(
            "🧪 Demonstrate Emergency Workflow"
        ):

            st.caption(
                "This button is only for your project demonstration."
            )

            if st.button(
                "🚨 TRIGGER EMERGENCY DEMO",
                use_container_width=True
            ):

                st.session_state.signal_lost = True

                st.rerun()

# =========================================================
# FOOTER
# =========================================================

st.markdown(textwrap.dedent("""    <div class="footer">
        🐰 LAST SIGNAL
        <br>
        Intelligent Personal Safety & Emergency Response
    </div>"""), unsafe_allow_html=True)

# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()
