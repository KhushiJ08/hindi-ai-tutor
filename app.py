import streamlit as st
from gemini_api import get_response
from db_manager import login_and_update_streak # Import our new function

st.title("🌾 Hindi AI Tutor")

# --- LOGIN SYSTEM ---
# We check if the user is already stored in the session state.
if "student_id" not in st.session_state:
    st.subheader("Login / Sign Up")
    name_input = st.text_input("Tumhara naam kya hai? (What is your name?)")
    
    if st.button("Start Learning"):
        if name_input:
            # Call our DB function
            s_id, streak = login_and_update_streak(name_input)
            
            # Save to Streamlit's temporary memory
            st.session_state["student_id"] = s_id
            st.session_state["student_name"] = name_input
            st.session_state["streak"] = streak
            st.rerun() # Refresh the page to hide the login screen
else:
    # --- MAIN TUTOR INTERFACE ---
    # Display the user's name and streak at the top
    st.success(f"Namaste, {st.session_state['student_name']}! 🙏 | 🔥 Current Streak: {st.session_state['streak']} Days")
    
    user_input = st.text_input("Apna doubt pucho...")

    if user_input:
        st.write("👨‍🎓 Tum:", user_input)
        
        with st.spinner("Tutor is thinking..."):
            response = get_response(user_input)
        
        st.write("🤖 Tutor:", response)
        
        # We will add the logic to track "weak concepts" here later!