# streamlit_app.py

import streamlit as st
import pandas as pd
import networkx as nx
import folium
import pymysql

from streamlit_folium import folium_static

# Initialize connection.

def init_connection():
    return pymysql.connect(**st.secrets["singlestore"])

conn = init_connection()

# Perform query.

connections_df = pd.read_sql("""
SELECT *
FROM london_connections;
""", conn)

stations_df = pd.read_sql("""
SELECT *
FROM london_stations
ORDER BY name;
""", conn)

stations_df.set_index("id", inplace = True)

st.subheader("Shortest Path")

from_name = st.sidebar.selectbox("From", stations_df["name"])
to_name = st.sidebar.selectbox("To", stations_df["name"])

graph = nx.Graph()

for connection_id, connection in connections_df.iterrows():
  station1_name = stations_df.loc[connection["station1"]]["name"]
  station2_name = stations_df.loc[connection["station2"]]["name"]
  graph.add_edge(station1_name, station2_name, time = connection["time"])

shortest_path = nx.shortest_path(graph, from_name, to_name, weight = "time")

shortest_path_df = pd.DataFrame({"name" : shortest_path})

merged_df = pd.merge(shortest_path_df, stations_df, how = "left", on = "name")

m = folium.Map(tiles = "Stamen Terrain")

sw = merged_df[["latitude", "longitude"]].min().values.tolist()
ne = merged_df[["latitude", "longitude"]].max().values.tolist()

m.fit_bounds([sw, ne])

for i in range(0, len(merged_df)):
  folium.Marker(
    location = [merged_df.iloc[i]["latitude"], merged_df.iloc[i]["longitude"]],
    popup = merged_df.iloc[i]["name"],
  ).add_to(m)

points = tuple(zip(merged_df.latitude, merged_df.longitude))

folium.PolyLine(points, color = "red", weight = 3, opacity = 1).add_to(m)

folium_static(m)

st.sidebar.write("Your Journey", shortest_path_df)
