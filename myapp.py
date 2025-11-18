import streamlit as st
import pandas as pd
import altair as alt

# Yhdistä MySQL
conn = st.connection("mysql", type="sql")

# --- 1. Näytä countries-taulukko ---
countries_df = conn.query("SELECT * FROM countries LIMIT 10;", ttl=600)
st.write("Dataa eri maista,  MySQL (Countries):")
st.dataframe(countries_df)

# --- 2. Hae värit ja laske esiintymät ---
colors_df = conn.query("SELECT color FROM flag_colors;", ttl=600)
color_counts = colors_df['color'].value_counts().reset_index()
color_counts.columns = ['color', 'count']

# --- 3. Donitsikaavio oikeilla väreillä ja reunaviivalla valkoiselle ---
color_map = {
    'blue': '#0000FF',
    'white': '#FFFFFF',
    'red': '#FF0000',
    'green': '#008000',
    'yellow': '#FFFF00',
    'black': '#000000',
    'orange': '#FFA500'
}

chart = alt.Chart(color_counts).mark_arc(innerRadius=50).encode(
    theta='count:Q',
    color=alt.Color('color:N', scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values()))),
    tooltip=['color', 'count'],
    stroke=alt.condition(
        alt.datum.color == 'white',  # Jos väri on valkoinen
        alt.value('#D3D3D3'),        # Vaaleanharmaa reunaviiva
        alt.value(None)              # Muuten ei reunaa
    ),
    strokeWidth=alt.condition(
        alt.datum.color == 'white',
        alt.value(2),                # Reunan paksuus
        alt.value(0)
    )
).properties(
    title='Maiden lippujen värien jakauma'
)

st.altair_chart(chart, use_container_width=True)
