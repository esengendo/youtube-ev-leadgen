import pandas as pd
import plotly.express as px
import os

LEADS_CSV = "data/leads.csv"
IMG_DIR = "visualizations"

def main():
    if not os.path.exists(LEADS_CSV):
        print("No leads data found.")
        return
    df = pd.read_csv(LEADS_CSV)
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df['date'] = df['Timestamp'].dt.date
        leads_over_time = df.groupby('date').size().reset_index(name='num_leads')
        fig = px.line(leads_over_time, x='date', y='num_leads', title='Leads Generated Over Time')
        os.makedirs(IMG_DIR, exist_ok=True)
        fig.write_html(f"{IMG_DIR}/leads_over_time.html")
        fig.show()
    else:
        print("No 'Timestamp' column found in leads data.")

if __name__ == "__main__":
    main()
