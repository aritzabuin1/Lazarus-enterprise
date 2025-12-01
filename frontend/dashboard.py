import streamlit as st
import requests
import pandas as pd

# Page config
st.set_page_config(
    page_title="Lazarus Enterprise",
    page_icon="🚀",
    layout="wide"
)

# Title
st.title("🚀 Lazarus Enterprise")
st.markdown("### Campaign Management Dashboard")
st.markdown("---")

# API Configuration
API_URL = "http://127.0.0.1:8000/campaign/upload"

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 Upload Campaign CSV")
    st.markdown("Upload a CSV file with `name` and `phone` columns to create a new campaign.")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="CSV must contain 'name' and 'phone' columns"
    )
    
    # Preview uploaded file
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, dtype=str)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.markdown("**Preview:**")
            st.dataframe(df.head(10), use_container_width=True)
            st.info(f"Total rows: {len(df)}")
            
            # Reset file pointer for upload
            uploaded_file.seek(0)
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

with col2:
    st.subheader("ℹ️ Instructions")
    st.markdown("""
    1. Prepare a CSV file with columns:
       - `name`: Lead name
       - `phone`: Phone number (E.164 format)
    
    2. Upload the file using the uploader
    
    3. Click **Launch Campaign** to start
    
    4. The system will:
       - Create leads in the database
       - Queue AI agent tasks
       - Start conversations automatically
    """)

# Launch button
st.markdown("---")
if uploaded_file is not None:
    if st.button("🚀 Launch Campaign", type="primary", use_container_width=True):
        with st.spinner("Uploading campaign..."):
            try:
                # Reset file pointer
                uploaded_file.seek(0)
                
                # Send to API
                files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                response = requests.post(API_URL, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"""
                    ✅ **Campaign Launched Successfully!**
                    
                    - **Campaign ID**: `{data.get('campaign_id', 'N/A')}`
                    - **Leads Queued**: {data.get('leads_queued', 0)}
                    - **Status**: {data.get('status', 'unknown')}
                    
                    {data.get('message', '')}
                    """)
                    st.balloons()
                else:
                    st.error(f"""
                    ❌ **Upload Failed**
                    
                    - **Status Code**: {response.status_code}
                    - **Error**: {response.text}
                    """)
            except requests.exceptions.ConnectionError:
                st.error("""
                ❌ **Connection Error**
                
                Cannot connect to the API server. Please ensure:
                1. The FastAPI server is running: `uvicorn app.main:app --reload`
                2. The server is accessible at `http://127.0.0.1:8000`
                """)
            except Exception as e:
                st.error(f"❌ **Unexpected Error**: {str(e)}")
else:
    st.info("👆 Please upload a CSV file to launch a campaign")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>Lazarus Enterprise | Powered by AI Agents</small>
</div>
""", unsafe_allow_html=True)
