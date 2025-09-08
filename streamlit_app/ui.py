import streamlit as st
import requests

st.title("FastAPI + Streamlit Demo")

# Document type selection
DOCUMENT_TYPES = ["medisave", "education"]
doc_type = st.selectbox("Select Document Type", DOCUMENT_TYPES)

# File upload
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "png", "jpg", "jpeg"])


import base64

if uploaded_file is not None:
    st.write(f"Uploaded file: {uploaded_file.name}")
    st.write(f"Selected document type: {doc_type}")

submit = st.button("Submit File")
if uploaded_file is not None and submit:
    file_bytes = uploaded_file.read()
    encoded_file = base64.b64encode(file_bytes).decode("utf-8")
    payload = {
        "documenttype": doc_type,
        "document": encoded_file
    }
    response = requests.post("http://localhost:8000/upload-document", json=payload)
    if response.status_code == 200:
        st.success(f"Upload successful: {response.json()}")
    else:
        st.error(f"Upload failed: {response.text}")

if st.button("Ping API"):
    response = requests.get("http://localhost:8000/ping")
    if response.status_code == 200:
        st.success(response.json()["message"])
    else:
        st.error("API not reachable")
