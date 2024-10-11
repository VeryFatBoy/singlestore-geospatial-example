# streamlit_app.py

import streamlit as st
import folium
import networkx as nx
import pandas as pd
import sqlalchemy
from streamlit_folium import st_folium

# Initialise connection.
conn = st.connection("singlestore", type = "sql")

stmt1 = """
SELECT station1, station2, time
FROM london_connections;
"""
connections_df = conn.query(stmt1)

stmt2 = """
SELECT id, name, latitude, longitude
FROM london_stations
ORDER BY name;
"""
stations_df = conn.query(stmt2)
stations_df.set_index("id", inplace = True)

st.subheader("Shortest Path")
from_name = st.sidebar.selectbox("From", stations_df["name"])
to_name = st.sidebar.selectbox("To", stations_df["name"])

graph = nx.Graph()
graph.add_weighted_edges_from(
    [(stations_df.loc[conn["station1"], "name"], stations_df.loc[conn["station2"], "name"], conn["time"]) 
     for _, conn in connections_df.iterrows()]
)

shortest_path = nx.shortest_path(graph, from_name, to_name, weight = "time")
shortest_path_df = pd.DataFrame({"name": shortest_path})

merged_df = shortest_path_df.join(stations_df.set_index("name"), on = "name")

initial_location = [merged_df.iloc[0]["latitude"], merged_df.iloc[0]["longitude"]]
m = folium.Map(location = initial_location, zoom_start = 13)

sw = merged_df[["latitude", "longitude"]].min().values.tolist()
ne = merged_df[["latitude", "longitude"]].max().values.tolist()
m.fit_bounds([sw, ne])

for i, row in merged_df.iterrows():
    folium.Marker(
        location = [row["latitude"], row["longitude"]],
        popup = row["name"]
    ).add_to(m)

folium.PolyLine(
    locations = merged_df[["latitude", "longitude"]].values.tolist(),
    color = "red",
    weight = 3,
    opacity = 1
).add_to(m)

st_folium(m)

st.sidebar.write("Your Journey", shortest_path_df)
