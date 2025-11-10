from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("sqlite:///extracted.db")

df = pd.read_sql("SELECT * FROM extracted", engine)
print(df.head())

df.to_csv("1msongs.csv")