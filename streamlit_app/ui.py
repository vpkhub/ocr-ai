import streamlit as st


import requests
import base64
import uuid
from ocr_validation import ocr_validation_ui

st.title("Dara OCR-AI Document Uploader")

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
        documentid = str(uuid.uuid4())
        st.info(f"Document ID for {uploaded_file.name}: {documentid}")
        payload = {
            "documenttype": doc_type,
            "document": encoded_file,
            "documentid": documentid
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
            "response": resp_json,
            "documentid": documentid
        })
        progress_bar.progress((idx + 1) / total)
    progress_bar.empty()
    return results

def upload_single_file(file, doc_type):
    file_bytes = file.read()
    encoded_file = base64.b64encode(file_bytes).decode("utf-8")
    documentid = str(uuid.uuid4())
    payload = {
        "documenttype": doc_type,
        "document": encoded_file,
        "documentid": documentid
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
    return response, elapsed, api_time, service_time, documentid




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
            # Generate and display documentid for this upload
            if 'single_docid' not in st.session_state or st.session_state['single_key'] != st.session_state.get('last_single_key', -1):
                st.session_state['single_docid'] = str(uuid.uuid4())
                st.session_state['last_single_key'] = st.session_state['single_key']
            st.info(f"Document ID: {st.session_state['single_docid']}")
            submit = st.button("Submit File")
            if submit:
                response, elapsed, api_time, service_time, documentid = upload_single_file(uploaded_file, doc_type)
                if response.status_code == 200:
                    st.session_state['single_result'] = (
                        f"Upload successful: {response.json()}",
                        f"API response time: {elapsed:.2f} seconds\nAPI function time: {api_time:.2f} s\nService function time: {service_time:.2f} s\nDocument ID: {documentid}",
                        True)
                else:
                    st.session_state['single_result'] = (
                        f"Upload failed: {response.text}",
                        f"API response time: {elapsed:.2f} seconds\nDocument ID: {documentid}",
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
    st.image("validation/sls_logo.gif", caption="SLS Logo", use_container_width=True)
    st.markdown("## Actions")
    clear = st.button("Clear Results", type="primary")
    if clear:
        st.session_state['results'] = None
        st.session_state['single_result'] = None
        st.session_state['single_key'] += 1
        st.session_state['multi_key'] += 1
        # Also clear validation section state
        st.session_state['ocr_validation_open'] = False
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
    # Display response as JSON and add download button
    if success:
        import json
        resp = st.session_state['single_result'][0]
        try:
            resp_json = response.json()
            st.json(resp_json)
            json_str = json.dumps(resp_json, indent=2)
            st.download_button("Download API Response as JSON", data=json_str, file_name="single_api_response.json", mime="application/json")
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
    # Display each response as JSON and collect for download
    import json
    all_responses = []
    for r in st.session_state['results']:
        if r['status'] == 'Success' and isinstance(r['response'], dict):
            st.json(r['response'])
            all_responses.append(r['response'])
    if all_responses:
        json_str = json.dumps(all_responses, indent=2)
        st.download_button("Download All API Responses as JSON", data=json_str, file_name="ocr_api_responses.json", mime="application/json")



# --- OCR Validation Section ---
if 'ocr_validation_open' not in st.session_state:
    st.session_state['ocr_validation_open'] = False

def open_ocr_validation():
    st.session_state['ocr_validation_open'] = True


# --- OCR Validation Section ---
with st.sidebar:
    open_val = st.button("Open OCR Validation Tool")
    if open_val:
        open_ocr_validation()

if st.session_state['ocr_validation_open']:
    ocr_validation_ui()

if st.button("Ping API"):
    response = requests.get("http://localhost:8000/ping")
    if response.status_code == 200:
        st.success(response.json()["message"])
    else:
        st.error("API not reachable")
