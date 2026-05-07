import streamlit as st
from gemini_api import get_response
from db_manager import login_and_update_streak, log_concept

st.title("🌾 Hindi AI Tutor")

# --- LOGIN SYSTEM ---
# We check if the user is already stored in the session state.
if "student_id" not in st.session_state:
    st.subheader("Login / Sign Up")
    name_input = st.text_input("Tumhara naam kya hai? (What is your name?)")
    
    if st.button("Start Learning"):
        if name_input:
            # Call our SQLite DB function to get ID and calculate streak
            s_id, streak = login_and_update_streak(name_input)
            
            # Save to Streamlit's permanent memory box
            st.session_state["student_id"] = s_id
            st.session_state["student_name"] = name_input
            st.session_state["streak"] = streak
            
            # Refresh the page to hide the login screen and show the tutor
            st.rerun() 
else:
    # --- MAIN TUTOR INTERFACE ---
    # Display the user's name and streak at the top
    st.success(f"Namaste, {st.session_state['student_name']}! 🙏 | 🔥 Current Streak: {st.session_state['streak']} Days")
    
    user_input = st.text_input("Apna doubt pucho...")

    if user_input:
        # 1. Show the student's question
        st.write("👨‍🎓 Tum:", user_input)
        
        with st.spinner("Tutor is thinking..."):
            # This now returns our structured JSON dictionary!
            response_data = get_response(user_input) 
        
        # 2. Display the Hindi response to the student
        st.write("🤖 Tutor:", response_data["tutor_response"])
        
        # 3. Silently log the weak topic in the background for the Teacher Panel
        if response_data["topic"] != "Error":
            log_concept(
                student_id=st.session_state["student_id"],
                concept_name=response_data["topic"],
                status=response_data["status"]
            )
            # A tiny pop-up to show the system is tracking data (great for your demo video!)
            st.toast(f"🧠 Tracked: {response_data['topic']} ({response_data['status']})")

    # Optional: A button to log out and clear the session
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()