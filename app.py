import streamlit as st
import face_recognition
import numpy as np
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# --- FIREBASE INITIALIZATION ---
if not firebase_admin._apps:
    # This logic allows it to work both on your laptop AND on the web
    if os.path.exists("secrets.json"):
        cred = credentials.Certificate("secrets.json")
    else:
        # This part is for when you upload to Streamlit Cloud
        fb_conf = st.secrets["firebase"]
        cred = credentials.Certificate(dict(fb_conf))
    
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- STYLING ---
st.set_page_config(page_title="VOTE-SHIELD AI", page_icon="🛡️")
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE FOR LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- LOGIN PAGE ---
if not st.session_state.authenticated:
    st.title("🛡️ VOTE-SHIELD LOGIN")
    user = st.text_input("Official Username")
    pw = st.text_input("Security Password", type="password")
    if st.button("Login"):
        if user == "admin" and pw == "india2026":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

# --- MAIN APP NAVIGATION ---
menu = ["Home", "Voter Enrollment", "Live Voting Booth", "Voter Registry"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Home":
    st.title("Welcome to Vote-Shield AI")
    st.write("Secure, Biometric-based Anti-Scam Election System.")
    st.image("https://img.icons8.com/clouds/200/000000/fingerprint.png")

# --- PHASE 1: ENROLLMENT ---
elif choice == "Voter Enrollment":
    st.header("👤 Mandatory Enrollment")
    aadh = st.text_input("Aadhaar Number (12 Digits)")
    name = st.text_input("Full Name")
    elec_id = st.text_input("Election Card Number")
    photo = st.camera_input("Capture Face Biometrics")
    
    if st.button("Sync to Cloud Registry"):
        if aadh and name and photo:
            with st.spinner("Processing Biometrics..."):
                img = face_recognition.load_image_file(photo)
                encodings = face_recognition.face_encodings(img)
                
                if len(encodings) > 0:
                    encoding_list = encodings[0].tolist()
                    db.collection("voters").document(aadh).set({
                        "name": name,
                        "aadhaar": aadh,
                        "election_id": elec_id,
                        "face_encoding": encoding_list,
                        "has_voted": False
                    })
                    st.success(f"✅ Voter {name} Registered Successfully!")
                else:
                    st.error("Face not detected. Try again.")

# --- PHASE 2: LIVE VOTING ---
elif choice == "Live Voting Booth":
    st.header("🗳️ Identity Verification Booth")
    scan = st.camera_input("Scan Face")
    
    if scan:
        live_img = face_recognition.load_image_file(scan)
        live_enc = face_recognition.face_encodings(live_img)
        
        if live_enc:
            voters_ref = db.collection("voters").stream()
            found = False
            
            for doc in voters_ref:
                voter = doc.to_dict()
                stored_enc = np.array(voter['face_encoding'])
                
                # ML Match (Tolerance 0.5 for high accuracy)
                match = face_recognition.compare_faces([stored_enc], live_enc[0], tolerance=0.5)
                
                if match[0]:
                    st.subheader(f"✅ Identity Verified: {voter['name']}")
                    if voter['has_voted']:
                        st.error("🚨 SCAM ALERT: This person has already voted!")
                    else:
                        if st.button("Authorize & Cast Vote"):
                            db.collection("voters").document(voter['aadhaar']).update({"has_voted": True})
                            st.balloons()
                            st.success("Vote Cast Successfully!")
                    found = True
                    break
            if not found:
                st.error("❌ Person not found in registry!")

# --- ADMIN LOGS ---
elif choice == "Voter Registry":
    st.header("📊 Master Database (Cloud)")
    voters = db.collection("voters").stream()
    data = [v.to_dict() for v in voters]
    if data:
        df = pd.DataFrame(data).drop(columns=['face_encoding'])
        st.table(df)
    else:
        st.write("No voters registered yet.")