import pandas as pd
import os
import glob
import numpy as np
import smtplib
from email.message import EmailMessage
from sqlalchemy import create_engine

# CONFIG
folder_path = 'data/'  # Folder with input files
output_file = 'final_report.xlsx'
email_enabled = False
db_enabled = True
db_type = 'sqlite'  # Options: 'sqlite', 'postgresql', 'mysql'
db_name = 'analytics_db.db'  # For SQLite
table_name = 'final_report'

# DB Connection Strings (edit for your DB)
db_config = {
    'sqlite': f'sqlite:///{db_name}',
    'postgresql': 'postgresql://user:password@localhost:5432/dbname',
    'mysql': 'mysql+pymysql://user:password@localhost:3306/dbname'
}

# 1️⃣ Auto-Clean Excel/CSV
def clean_data(file_path):
    df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
    df.dropna(how='all', inplace=True)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return df

# 2️⃣ Merge Multiple Sheets/Files
def merge_files(path):
    all_files = glob.glob(os.path.join(path, "*.xlsx")) + glob.glob(os.path.join(path, "*.csv"))
    df_list = [clean_data(f) for f in all_files]
    merged_df = pd.concat(df_list, ignore_index=True)
    return merged_df

# 3️⃣ Summary + Outliers
def summary_and_outliers(df, column):
    summary = df[column].describe()
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    outliers = df[(df[column] < Q1 - 1.5*IQR) | (df[column] > Q3 + 1.5*IQR)]
    return summary, outliers

# 4️⃣ Export to Excel
def export_to_excel(df, summary, outliers, filename):
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Cleaned_Data', index=False)
        summary.to_frame().to_excel(writer, sheet_name='Summary')
        outliers.to_excel(writer, sheet_name='Outliers', index=False)

# 5️⃣ Optional Email Report
def send_email_report(file_path):
    msg = EmailMessage()
    msg['Subject'] = 'Auto-generated Report'
    msg['From'] = 'you@example.com'
    msg['To'] = 'stakeholder@example.com'
    msg.set_content('Hey! Attached is your automated report 📊')
    with open(file_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=output_file)
    
    with smtplib.SMTP('smtp.example.com', 587) as smtp:
        smtp.starttls()
        smtp.login('you@example.com', 'yourpassword')
        smtp.send_message(msg)

# 6️⃣ Push to SQL Database
def push_to_database(df):
    engine = create_engine(db_config[db_type])
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"📦 Data pushed to {db_type} database → table `{table_name}`")

# ▶️ Main Run
if __name__ == "__main__":
    df = merge_files(folder_path)
    summary, outliers = summary_and_outliers(df, column='amount' if 'amount' in df.columns else df.columns[-1])
    
    export_to_excel(df, summary, outliers, output_file)
    
    if db_enabled:
        push_to_database(df)
    
    if email_enabled:
        send_email_report(output_file)

    print("✅ Report generated and tasks completed!")
