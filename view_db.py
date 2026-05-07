import sqlite3

import pandas as pd

DB_PATH = "data/offers.db"
DISPLAY_COLUMNS = [
    "source",
    "title",
    "laboratory",
    "location",
    "deadline",
    "contact",
    "link",
]

conn = sqlite3.connect(DB_PATH)

query = f"""
SELECT {", ".join(DISPLAY_COLUMNS)}
FROM offers
WHERE source IS NOT NULL AND TRIM(source) != ''
ORDER BY source ASC, COALESCE(NULLIF(deadline, ''), '9999-12-31') ASC
"""

df = pd.read_sql_query(query, conn)
conn.close()

if df.empty:
    print("Aucune offre récente avec source non vide.")
else:
    print(df.to_string(index=False))
