import streamlit as st
from datetime import date
from gmail_fetcher import GmailFetcher
from qa_engine import QAEngine
import traceback

# Global objects (initialized once)
# Authentication happens implicitly when GmailFetcher is initialized
# We use st.session_state for engine to ensure it persists across reruns, though global is often fine too.
if 'fetcher' not in st.session_state:
    st.session_state.fetcher = GmailFetcher()
if 'engine' not in st.session_state:
    st.session_state.engine = QAEngine()

# Initializing session state variables
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'emails_fetched' not in st.session_state:
    st.session_state.emails_fetched = 0

st.title("📧 Gmail Summarization App (Groq LLM)")

# ---Authentication ---
st.header("1. Authentication Status")
st.info("The app will open a browser window for Google sign-in on first run. Please grant permissions.")
st.success("Google API service initialized.")

# ---Fetching and Summarizing Emails ---
st.header("2. Select Day and Summarize Emails")
selected_date = st.date_input("Select a day to summarize:", date.today())
date_str = selected_date.strftime('%Y-%m-%d')

# The button now triggers the entire process
if st.button(f"Fetch & Summarize Emails for {date_str}"):
    st.session_state.summary = None
    st.session_state.emails_fetched = 0
    
    with st.spinner(f"Fetching emails for {date_str}..."):
        try:
            # 1. Fetch Emails
            # Access fetcher from session state
            emails = st.session_state.fetcher.get_emails_for_day(date_str) 
            st.session_state.emails_fetched = len(emails)
            st.success(f"Fetched {len(emails)} emails.")
            
            if emails:
                # 2. Setup the Summarization Chain and Generate Summary
                with st.spinner("Analyzing emails and preparing summary..."):
                    # Access engine from session state
                    st.session_state.engine.setup_summarization_chain(emails) 
                    
                    # 3. Generate Summary
                    summary_result = st.session_state.engine.get_summary()
                    
                    # Check for expected dictionary key 'summary'
                    if "summary" in summary_result:
                        st.session_state.summary = summary_result["summary"]
                        st.success("Summarization complete!")
                    else:
                        st.error("Summarization returned an unexpected format. Check the terminal/logs.")

            else:
                st.warning("No emails found for the selected date. Nothing to summarize.")

        except Exception as e:
            # --- CRITICAL DEBUGGING OUTPUT ---
            st.error(f"An **ERROR** occurred during summarization or fetching: **{e}**")
            st.code(traceback.format_exc(), language='text')
            # --- END DEBUGGING OUTPUT ---


# --- Step 3: Display Summary ---
if st.session_state.summary:
    st.header(f"3. Summary of {st.session_state.emails_fetched} Emails")
    
    # Use st.markdown because the LLM prompt asks for structured bullet points
    st.markdown(st.session_state.summary)

    # Optional: Display the raw number of emails processed
    st.markdown(f"--- \n*Total emails processed: {st.session_state.emails_fetched}*")