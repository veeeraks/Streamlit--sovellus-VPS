import streamlit as st
import pandas as pd


# Use secrets to connect to MySQL
conn = st.connection("mysql", type="sql")

# Example query
df = conn.query("SELECT * FROM countries LIMIT 10;", ttl=600)

st.write("Data from MySQL:")
st.dataframe(df)
