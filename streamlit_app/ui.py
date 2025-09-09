import streamlit as st
import requests
import base64



st.markdown("""
<h1 style='text-align: center; color: #4F8BF9;'>OCR-AI Document Uploader</h1>
<hr style='border: 1px solid #4F8BF9;'>
""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; color: #888;'>Upload your document(s) for processing. Choose single or multiple file mode.</div>
""", unsafe_allow_html=True)

st.write("")

# UI mode selection
mode = st.radio("Choose upload mode", ("Single File", "Multiple Files"), horizontal=True)

# Document type selection
DOCUMENT_TYPES = ["medisave", "education"]
doc_type = st.selectbox("Select Document Type", DOCUMENT_TYPES)


import time


def upload_multiple_files(files, doc_type):
    """Uploads multiple files to the API and returns timing/results, with progress bar."""
    results = []
    progress_bar = st.progress(0)
    total = len(files)
    for idx, uploaded_file in enumerate(files):
        file_bytes = uploaded_file.read()
        encoded_file = base64.b64encode(file_bytes).decode("utf-8")
        payload = {
            "documenttype": doc_type,
            "document": encoded_file
        }
        start_time = time.time()
        response = requests.post("http://localhost:8000/upload-document", json=payload)
        elapsed = time.time() - start_time
        if response.status_code == 200:
            resp_json = response.json()
            api_time = resp_json.get("api_time", None)
            service_time = resp_json.get("service_time", None)
        else:
            resp_json = response.text
            api_time = None
            service_time = None
        results.append({
            "filename": uploaded_file.name,
            "status": "Success" if response.status_code == 200 else "Failed",
            "response_time": elapsed,
            "api_time": api_time,
            "service_time": service_time,
            "response": resp_json
        })
        progress_bar.progress((idx + 1) / total)
    progress_bar.empty()
    return results

def upload_single_file(file, doc_type):
    file_bytes = file.read()
    encoded_file = base64.b64encode(file_bytes).decode("utf-8")
    payload = {
        "documenttype": doc_type,
        "document": encoded_file
    }
    start_time = time.time()
    response = requests.post("http://localhost:8000/upload-document", json=payload)
    elapsed = time.time() - start_time
    if response.status_code == 200:
        resp_json = response.json()
        api_time = resp_json.get("api_time", None)
        service_time = resp_json.get("service_time", None)
    else:
        api_time = None
        service_time = None
    return response, elapsed, api_time, service_time




# Session state for clearing and uploader keys
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None
if 'single_key' not in st.session_state:
    st.session_state['single_key'] = 0
if 'multi_key' not in st.session_state:
    st.session_state['multi_key'] = 0


col1, col2 = st.columns([1, 1])

with col1:
    if mode == "Single File":
        uploaded_file = st.file_uploader("Upload a file", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=False, key=st.session_state['single_key'])
        if uploaded_file is not None:
            st.write(f"**Selected:** {uploaded_file.name}")
            st.write(f"**Document type:** {doc_type}")
            submit = st.button("Submit File")
            if submit:
                response, elapsed, api_time, service_time = upload_single_file(uploaded_file, doc_type)
                if response.status_code == 200:
                    st.session_state['single_result'] = (
                        f"Upload successful: {response.json()}",
                        f"API response time: {elapsed:.2f} seconds\nAPI function time: {api_time:.2f} s\nService function time: {service_time:.2f} s",
                        True)
                else:
                    st.session_state['single_result'] = (
                        f"Upload failed: {response.text}",
                        f"API response time: {elapsed:.2f} seconds",
                        False)
    elif mode == "Multiple Files":
        uploaded_files = st.file_uploader("Upload files", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True, key=st.session_state['multi_key'])
        if uploaded_files:
            st.write(f"**{len(uploaded_files)} files selected.**")
            st.write(f"**Document type:** {doc_type}")
            submit = st.button("Submit Files")
            if submit:
                results = upload_multiple_files(uploaded_files, doc_type)
                st.session_state['results'] = results

# Move Clear Results button to sidebar
with st.sidebar:
    st.markdown("## Actions")
    clear = st.button("Clear Results", type="primary")
    if clear:
        st.session_state['results'] = None
        st.session_state['single_result'] = None
        st.session_state['single_key'] += 1
        st.session_state['multi_key'] += 1
        st.rerun()

# Show results
if mode == "Single File" and st.session_state['single_result']:
    msg, info, success = st.session_state['single_result']
    if success:
        st.success(msg)
    else:
        st.error(msg)
    for line in info.split("\n"):
        st.info(line)
    # Display response as JSON
    if success:
        import json
        resp = st.session_state['single_result'][0]
        try:
            # Try to pretty print the JSON part of the message
            resp_json = response.json()
            st.json(resp_json)
        except Exception:
            pass
elif mode == "Multiple Files" and st.session_state['results']:
    st.write("## Results")
    st.table([
        {
            "File": r["filename"],
            "Status": r["status"],
            "Response Time (s)": f"{r['response_time']:.2f}",
            "API Time (s)": f"{r['api_time']:.2f}" if r['api_time'] is not None else "-",
            "Service Time (s)": f"{r['service_time']:.2f}" if r['service_time'] is not None else "-",
            "Response": r["response"]
        } for r in st.session_state['results']
    ])
    # Display each response as JSON
    import json
    for r in st.session_state['results']:
        if r['status'] == 'Success' and isinstance(r['response'], dict):
            st.json(r['response'])

if st.button("Ping API"):
    response = requests.get("http://localhost:8000/ping")
    if response.status_code == 200:
        st.success(response.json()["message"])
    else:
        st.error("API not reachable")
