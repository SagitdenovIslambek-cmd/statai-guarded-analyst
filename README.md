# StatAI Streamlit Starter

This is a starter UI for the StatAI Guarded Analyst project.

## What it does
- Provides a Streamlit web interface.
- Accepts uploaded T001 CSV files.
- Offers a few predefined statistical questions.
- Checks for expected columns before calculation.
- Calculates simple shares with pandas and shows tables/charts.
- Explains methodology and limitations.

## Important limitations
- This is a prototype, not a fully integrated generative AI system.
- The current planner uses predefined choices, not free-form LLM interpretation.
- Do not present synthetic microdata results as official population estimates.
- Confirm code meanings in the official codebook before interpreting categories.
- Do not upload unrelated data families as T001.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
For public sharing, put `app.py` and `requirements.txt` in a GitHub repository, then deploy it through Streamlit Community Cloud. Do not commit API keys or other secrets to GitHub.
