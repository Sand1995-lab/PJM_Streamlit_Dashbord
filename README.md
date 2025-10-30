# ⚡ PJM Zone-wise Load — Dark Dashboard

A minimal, aesthetic, **dark theme** dashboard for exploring PJM zone-wise electricity load.  
Designed to be **student-friendly (Class 10+)** with simple explanations and interactive charts.

## Preview

- Trend over time for selected zones
- Top/Bottom zones by average load
- Daily averages and hourly patterns
- Helpful explanations in plain language

## Project Structure

```
pjm-dark-dashboard/
├─ app.py
├─ requirements.txt
├─ .streamlit/
│  └─ config.toml
└─ data/
   └─ PJM-ZONE-WISE-LOAD-DATA.xlsx
```

## How to Run Locally

1. **Install dependencies** (ideally in a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the app**:
   ```bash
   streamlit run app.py
   ```
3. Open the link that appears in your terminal (usually `http://localhost:8501`).

## Deploy to Streamlit Cloud

1. Push this folder to a **public GitHub repo**.
2. On [Streamlit Community Cloud], create a new app pointing to `app.py` in your repo.
3. Make sure the `data/PJM-ZONE-WISE-LOAD-DATA.xlsx` file is included (or change the path in `app.py`).

## Data

Place your Excel file at `data/PJM-ZONE-WISE-LOAD-DATA.xlsx`.  
If your sheet name differs, the app will load the **first sheet** automatically.

## Notes for Students

- **Load (MW)** means how much power is used. 1,000 MW can power a large city.
- Lines go **up** when people use more electricity (hot afternoons or cold mornings).
- Lines go **down** late at night when most people sleep.

---

Made with ❤️ using Streamlit + Plotly.