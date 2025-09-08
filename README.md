# FastAPI + Streamlit Project

## Structure

- `app/`: FastAPI backend
  - `main.py`: FastAPI entry point
  - `api.py`: API endpoints
- `streamlit_app/`: Streamlit UI
  - `ui.py`: Streamlit app
- `requirements.txt`: Dependencies

## How to Run

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

2. Start FastAPI backend:
   ```sh
   uvicorn app.main:app --reload
   ```

3. In a new terminal, start Streamlit UI:
   ```sh
   streamlit run streamlit_app/ui.py
   ```

4. Use the Streamlit UI to interact with the FastAPI backend.
