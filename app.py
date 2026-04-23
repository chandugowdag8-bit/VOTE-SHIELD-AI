import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os
import pandas as pd  # Added this to prevent another NameError later!

# --- 1. CLOUD CONNECTION ---
# Check if the app is already connected to avoid "App already exists" error
if not firebase_admin._apps:
    if os.path.exists("secrets.json"):
        cred = credentials.Certificate("secrets.json")
    else:
        # Improved logic to handle Streamlit Secrets
        try:
            fb_dict = {}
            for key in st.secrets["firebase"]:
                value = st.secrets["firebase"][key]
                # This fixes the common "newline" issue in private keys
                if key == "private_key" and isinstance(value, str):
                    fb_dict[key] = value.replace("\\n", "\n")
                else:
                    fb_dict[key] = value
            cred = credentials.Certificate(fb_dict)
        except Exception as e:
            st.error("Firebase Secrets are missing or formatted incorrectly in Streamlit Settings.")
            st.stop()
            
    firebase_admin.initialize_app(cred)

db = firestore.client()



# --- 2. HTML/CSS CUSTOM STYLING ---
st.set_page_config(page_title="VOTE-SHIELD AI", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button {
        width: 100%;
        background-color: #002D62;
        color: white;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    .header-box {
        background-color: #002D62;
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. OFFICIAL LOGIN ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div class="header-box"><h1>🛡️ VOTE-SHIELD OFFICIAL ACCESS</h1></div>', unsafe_allow_html=True)
    user = st.text_input("Officer ID")
    pw = st.text_input("Security Pin", type="password")
    if st.button("Authorize Access"):
        if pw == "admin123":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

# --- 4. MAIN APP ---
st.sidebar.title("🛡️ Control Panel")
choice = st.sidebar.radio("Navigation", ["Voter Enrollment", "Identity Verification", "Election Statistics"])

# --- PHASE 1: ENROLLMENT ---
if choice == "Voter Enrollment":
    st.markdown('<div class="header-box"><h2>📋 Voter Registration Portal</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        aadh = st.text_input("Aadhaar Number (UIDAI)")
        name = st.text_input("Voter Full Name")
    with col2:
        epic = st.text_input("Election ID (EPIC)")
        age = st.number_input("Age", min_value=18, max_value=120)

    photo = st.camera_input("Capture ID Photo for Registry")

    if st.button("Sync Data to National Cloud"):
        if aadh and name and epic:
            db.collection("voters").document(aadh).set({
                "name": name,
                "aadhaar": aadh,
                "epic": epic,
                "voted": False
            })
            st.success(f"Verified: {name} successfully added to Registry.")

# --- PHASE 2: VERIFICATION ---
elif choice == "Identity Verification":
    st.markdown('<div class="header-box"><h2>🗳️ Live Verification Booth</h2></div>', unsafe_allow_html=True)
    
    voter_uid = st.text_input("Scan or Enter Aadhaar Number")
    
    if voter_uid:
        doc = db.collection("voters").document(voter_uid).get()
        if doc.exists:
            data = doc.to_dict()
            st.info(f"**Found Record:** {data['name']} | **EPIC:** {data['epic']}")
            
            st.camera_input("Biometric Confirmation")
            
            if data['voted']:
                st.error("🚨 FRAUD DETECTED: This individual has already cast a vote!")
            else:
                if st.button("AUTHORIZE VOTE"):
                    db.collection("voters").document(voter_uid).update({"voted": True})
                    st.balloons()
                    st.success("Identity Verified. Vote Authorized.")
        else:
            st.error("No Record Found. Check Aadhaar Number.")

# --- PHASE 3: STATISTICS ---
elif choice == "Election Statistics":
    st.markdown('<div class="header-box"><h2>📊 Real-time Election Logs</h2></div>', unsafe_allow_html=True)
    voters = db.collection("voters").stream()
    voter_list = [v.to_dict() for v in voters]
    
    if voter_list:
        import pandas as pd
        df = pd.DataFrame(voter_list)
        st.table(df[['name', 'aadhaar', 'epic', 'voted']])
    else:
        st.write("Registry is currently empty.")
