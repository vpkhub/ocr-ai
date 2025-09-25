#!/bin/bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 &
streamlit run streamlit_app/ui.py --server.port 8501 --server.address 0.0.0.0