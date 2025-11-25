import streamlit as st
import pandas as pd
import altair as alt
import requests
import random
from math import radians, sin, cos, sqrt, atan2
from streamlit_autorefresh import st_autorefresh  # <-- uusi kirjasto

# --- Automaattinen päivitys 10 min välein ---
st_autorefresh(interval=600000, limit=None, key="weather_refresh")  # 600000 ms = 10 min

# --- FUNKTIOT ---
def get_coords(place):
    url = f"https://nominatim.openstreetmap.org/search?q={place}&format=json"
    headers = {"User-Agent": "Cron_assignment (esim@gmail.com)"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except ValueError:
            st.error("Virhe: Vastauksessa ei ollut JSON-dataa.")
    else:
        st.error(f"Nominatim API virhe: {response.status_code}")
    return None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# --- SATUNNAISET KAUPUNGIT ---
cities = [
    "Helsinki", "Stockholm", "Oslo", "Tokyo", "Brasília",
    "Ottawa", "Nairobi", "Canberra", "Washington D.C.", "New Delhi"
]

# --- SIVUN OTSIKKO ---
st.title("Tampereen sää ja muiden maiden dataa")

# --- Satunnainen kaupunki heti sivun latauksessa ---
if "random_city" not in st.session_state:
    st.session_state.random_city = random.choice(cities)
    tampere_coords = get_coords("Tampere")
    city_coords = get_coords(st.session_state.random_city)
    if tampere_coords and city_coords:
        st.session_state.distance = haversine(*tampere_coords, *city_coords)

# --- VÄLILEHDET ---
tab1, tab2, tab3 = st.tabs(["🌤 Sää", "🌍 Maatiedot", "📍 Etäisyydet"])

# --- SÄÄDATA ---
with tab1:
    st.subheader("🌤 Säädata")
    weather_conn = st.connection("mysql_weather", type="sql")

    # Hae säädata (autorefresh hoitaa päksen)
    weather_df = weather_conn.query(
        "SELECT city, temperature, description, timestamp FROM weather_data ORDER BY timestamp DESC LIMIT 50;",
        ttl=600
    )

    # Muunna timestamp datetime-muotoon ja lisää +2h
    weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp']) + pd.Timedelta(hours=2)

    # Näytä metric-kortit (viimeisimmät arvot)
    st.write("### Viimeisimmät säätiedot")
    latest_df = weather_df.groupby('city').first().reset_index()
    cols = st.columns(len(latest_df))
    for i, row in latest_df.iterrows():
        with cols[i]:
            st.metric(label=row["city"], value=f"{row['temperature']}°C", delta=row["description"])

    # Resamplaus 15 min välein (vain lämpötila)
    resampled_list = []
    for city in weather_df['city'].unique():
        city_data = weather_df[weather_df['city'] == city].set_index('timestamp')
        city_resampled = city_data['temperature'].resample('15T').mean().reset_index()
        city_resampled['city'] = city
        resampled_list.append(city_resampled)

    resampled_df = pd.concat(resampled_list)

    # Viivakaavio lämpötiloista ajan mukaan
    st.write("### Lämpötila (15 min välein)")
    line_chart = alt.Chart(resampled_df).mark_line(point=True).encode(
        x=alt.X('timestamp:T',
                axis=alt.Axis(format='%H:%M', tickCount=15),
                title='Aika (Suomen aika)'),
        y=alt.Y('temperature:Q', title='Lämpötila (°C)'),
        color='city:N',
        tooltip=['city', 'temperature', 'timestamp']
    ).properties(
        title='Lämpötilan muutos Tampereella'
    )

    st.altair_chart(line_chart, use_container_width=True)

# --- MAATIEDOT ---
with tab2:
    st.subheader("Maatiedot")
    countries_conn = st.connection("mysql_countries", type="sql")
    countries_df = countries_conn.query("SELECT * FROM countries LIMIT 10;", ttl=600)
    st.dataframe(countries_df)

    # Lipun värien donitsikaavio
    colors_df = countries_conn.query("SELECT color FROM flag_colors;", ttl=600)
    color_counts = colors_df['color'].value_counts().reset_index()
    color_counts.columns = ['color', 'count']

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
            alt.datum.color == 'white',
            alt.value('#D3D3D3'),
            alt.value(None)
        ),
        strokeWidth=alt.condition(
            alt.datum.color == 'white',
            alt.value(2),
            alt.value(0)
        )
    ).properties(
        title='Maiden lippujen värien jakauma'
    )

    st.altair_chart(chart, use_container_width=True)


# --- ETÄISYYS ---
with tab3:
    st.subheader("Tampereelta maailmalle")

    # Näytetään nykyinen arvottu kaupunki ja etäisyys
    st.write(f"Satunnainen kaupunki: **{st.session_state.random_city}**")
    st.write(f"Etäisyys Tampereesta: **{st.session_state.distance:.2f} km**")

    # Nappi uuden kaupungin arpomiseen
    if st.button("🎲 Arvo uusi kaupunki"):
        st.session_state.random_city = random.choice(cities)
        tampere_coords = get_coords("Tampere")
        city_coords = get_coords(st.session_state.random_city)
        if tampere_coords and city_coords:
            st.session_state.distance = haversine(*tampere_coords, *city_coords)
        st.rerun()
