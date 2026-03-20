# views/geo_viz.py  –  original code, unchanged
import pandas as pd
import os
import time
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pydeck as pdk
import streamlit as st

GEOCACHE = "geocache.csv"

def load_geocache():
    if os.path.exists(GEOCACHE):
        try:
            return pd.read_csv(GEOCACHE)
        except Exception:
            return pd.DataFrame(columns=["query", "lat", "lon"])
    return pd.DataFrame(columns=["query", "lat", "lon"])

def save_geocache(df):
    try:
        df.to_csv(GEOCACHE, index=False)
    except Exception:
        pass

def geocode_place(place, geolocator, geocode_fn, cache_df):
    if not place:
        return None, None
    existing = cache_df[cache_df['query'].str.lower() == str(place).lower()]
    if not existing.empty:
        try:
            return float(existing.iloc[0]['lat']), float(existing.iloc[0]['lon'])
        except Exception:
            pass
    try:
        location = geocode_fn(place)
        if location:
            lat, lon = location.latitude, location.longitude
            try:
                cache_df.loc[len(cache_df)] = [place, lat, lon]
            except Exception:
                cache_df = pd.concat(
                    [cache_df, pd.DataFrame([{"query": place, "lat": lat, "lon": lon}])],
                    ignore_index=True,
                )
            save_geocache(cache_df)
            time.sleep(0.5)
            return lat, lon
    except Exception:
        return None, None
    return None, None

def map_markets(df, place_col='market', state_col='state', n_points=200):
    if df is None or df.empty:
        st.info("No data to map.")
        return

    cache_df = load_geocache()
    geolocator = Nominatim(user_agent="farmora_geocoder")
    geocode_fn = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=2)

    coords = []
    used   = set()
    for idx, row in df.iterrows():
        if len(coords) >= n_points:
            break
        attempts = [
            f"{row.get(place_col,'')}, {row.get('district','')}, {row.get(state_col,'')}",
            f"{row.get('district','')}, {row.get(state_col,'')}",
            f"{row.get(place_col,'')}, {row.get(state_col,'')}",
            f"{row.get(place_col,'')}, India",
            f"{row.get('district','')}, India",
            f"{row.get(state_col,'')}, India",
        ]
        for attempt in attempts:
            attempt = attempt.strip(', ')
            if not attempt:
                continue
            key = attempt.lower()
            if key in used:
                continue
            lat, lon = geocode_place(attempt, geolocator, geocode_fn, cache_df)
            if lat and lon:
                coords.append({
                    "market":   row.get(place_col, ''),
                    "district": row.get('district', ''),
                    "state":    row.get(state_col, ''),
                    "lat": lat,
                    "lon": lon,
                })
                used.add(key)
                break

    if not coords:
        st.warning("Could not geocode any locations. Try a smaller selection or check network.")
        return

    mdf     = pd.DataFrame(coords)
    mid_lat = float(mdf['lat'].mean())
    mid_lon = float(mdf['lon'].mean())

    st.write(f"Showing {len(mdf)} geocoded markets.")

    scatter = pdk.Layer(
        "ScatterplotLayer",
        data=mdf,
        get_position='[lon, lat]',
        get_fill_color='[255, 120, 0, 160]',
        get_radius=3000,
        pickable=True,
    )
    tooltip    = {"html": "<b>Market:</b> {market}<br/><b>District:</b> {district}<br/><b>State:</b> {state}", "style": {"color": "white"}}
    view_state = pdk.ViewState(latitude=mid_lat, longitude=mid_lon, zoom=5, pitch=0)
    r          = pdk.Deck(layers=[scatter], initial_view_state=view_state, tooltip=tooltip)
    st.pydeck_chart(r)
