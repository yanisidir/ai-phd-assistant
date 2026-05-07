import os
import sqlite3
import sys

import pandas as pd
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from processing.parser import update_status
from processing.scorer import load_profile

DB_PATH = "data/offers.db"
STATUS_VALUES = ["to_apply", "applied", "rejected", "accepted"]
TABLE_COLUMNS = [
    "source",
    "title",
    "laboratory",
    "location",
    "deadline",
    "contact",
    "score",
    "decision",
    "status",
]

DETAIL_COLUMNS = TABLE_COLUMNS + ["link", "description"]


@st.cache_data(ttl=30)
def load_offers():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM offers", conn)
    finally:
        conn.close()

    if "source" not in df.columns:
        return pd.DataFrame(columns=DETAIL_COLUMNS)

    df = df[df["source"].fillna("").str.strip() != ""].copy()

    if "status" in df.columns:
        df["status"] = df["status"].fillna("").replace({"": "to_apply", "à faire": "to_apply"})

    for column in DETAIL_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df["deadline_sort"] = pd.to_datetime(df["deadline"], errors="coerce")
    df = df.sort_values(["source", "deadline_sort", "title"], na_position="last")
    return df.drop(columns=["deadline_sort"])


@st.cache_data(ttl=30)
def load_candidate_profile():
    return load_profile()


st.set_page_config(page_title="AI PhD Assistant", layout="wide")
st.title("AI PhD Application Assistant")

profile = load_candidate_profile()

with st.expander("Profil candidat", expanded=False):
    st.write("**Intérêts :**", ", ".join(profile.get("interests", [])))
    st.write(
        "**Intérêts négatifs :**",
        ", ".join(profile.get("negative_interests", [])),
    )
    if st.button("Recharger profil"):
        st.cache_data.clear()
        st.rerun()

df = load_offers()

if df.empty:
    st.info("Aucune offre sauvegardée avec une source non vide.")
    st.stop()

left, middle, right = st.columns(3)

with left:
    source_options = ["Toutes"] + sorted(df["source"].dropna().unique().tolist())
    selected_source = st.selectbox("Source", source_options)

with middle:
    status_options = ["Tous"] + STATUS_VALUES
    selected_status = st.selectbox("Statut", status_options)

with right:
    decision_options = ["Toutes"] + sorted(df["decision"].fillna("").replace("", "non renseigné").unique().tolist())
    selected_decision = st.selectbox("Décision", decision_options)

only_to_apply = st.checkbox("Voir seulement to_apply")

filtered_df = df.copy()

if selected_source != "Toutes":
    filtered_df = filtered_df[filtered_df["source"] == selected_source]

if only_to_apply:
    filtered_df = filtered_df[filtered_df["status"] == "to_apply"]
elif selected_status != "Tous":
    filtered_df = filtered_df[filtered_df["status"] == selected_status]

if selected_decision != "Toutes":
    if selected_decision == "non renseigné":
        filtered_df = filtered_df[filtered_df["decision"].fillna("").str.strip() == ""]
    else:
        filtered_df = filtered_df[filtered_df["decision"] == selected_decision]

st.subheader(f"Offres sauvegardées ({len(filtered_df)})")
st.dataframe(
    filtered_df[TABLE_COLUMNS],
    use_container_width=True,
    hide_index=True,
)

if filtered_df.empty:
    st.info("Aucune offre ne correspond aux filtres sélectionnés.")
    st.stop()

selection_labels = (
    filtered_df["source"].fillna("")
    + " | "
    + filtered_df["title"].fillna("")
)
selected_label = st.selectbox("Choisir une offre", selection_labels.tolist())
selected_index = selection_labels[selection_labels == selected_label].index[0]
selected_offer = filtered_df.loc[selected_index]

st.subheader("Détail de l'offre")

st.write("**Source :**", selected_offer.get("source", ""))
st.write("**Titre :**", selected_offer.get("title", ""))
st.write("**Laboratoire :**", selected_offer.get("laboratory", ""))
st.write("**Localisation :**", selected_offer.get("location", ""))
st.write("**Deadline :**", selected_offer.get("deadline", ""))
st.write("**Contact :**", selected_offer.get("contact", ""))
st.write("**Score :**", selected_offer.get("score", ""))
st.write("**Décision :**", selected_offer.get("decision", ""))
current_status = selected_offer.get("status", "to_apply")
if current_status not in STATUS_VALUES:
    current_status = "to_apply"

new_status = st.selectbox(
    "Statut de candidature",
    STATUS_VALUES,
    index=STATUS_VALUES.index(current_status),
)

link = selected_offer.get("link", "")
if new_status != selected_offer.get("status", "") and link:
    update_status(link, new_status)
    st.cache_data.clear()
    st.success("Statut mis à jour")
    st.rerun()

link = selected_offer.get("link", "")
if link:
    st.markdown(f"**Lien :** [{link}]({link})")
else:
    st.write("**Lien :**")

st.text_area(
    "Description complète",
    selected_offer.get("description", ""),
    height=320,
)
