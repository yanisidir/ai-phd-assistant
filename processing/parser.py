import sqlite3

from processing.scorer import score_offer_simple

DB_PATH = "data/offers.db"
STATUS_VALUES = {"to_apply", "applied", "rejected", "accepted"}

OFFER_COLUMNS = {
    "title": "TEXT",
    "link": "TEXT UNIQUE",
    "description": "TEXT",
    "source": "TEXT",
    "laboratory": "TEXT",
    "location": "TEXT",
    "deadline": "TEXT",
    "contact": "TEXT",
    "score": "INTEGER",
    "summary": "TEXT",
    "decision": "TEXT",
    "email": "TEXT",
    "status": "TEXT",
}


def _get_existing_columns(cursor):
    cursor.execute("PRAGMA table_info(offers)")
    return {row[1] for row in cursor.fetchall()}


def _migrate_offers_table(cursor):
    existing_columns = _get_existing_columns(cursor)

    for column, column_type in OFFER_COLUMNS.items():
        if column in existing_columns:
            continue

        # SQLite cannot add a UNIQUE column with ALTER TABLE.
        alter_type = "TEXT" if column == "link" else column_type
        cursor.execute(f"ALTER TABLE offers ADD COLUMN {column} {alter_type}")


def normalize_status(status):
    if status in STATUS_VALUES:
        return status
    return "to_apply"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        link TEXT UNIQUE,
        description TEXT,
        source TEXT,
        laboratory TEXT,
        location TEXT,
        deadline TEXT,
        contact TEXT,
        score INTEGER,
        summary TEXT,
        decision TEXT,
        email TEXT,
        status TEXT
    )
    """)

    _migrate_offers_table(cursor)
    cursor.execute("""
    UPDATE offers
    SET status = 'to_apply'
    WHERE status IS NULL
       OR TRIM(status) = ''
       OR status NOT IN ('to_apply', 'applied', 'rejected', 'accepted')
    """)

    conn.commit()
    conn.close()


def save_offer(offer, analysis):
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO offers (
        title, link, description, source, laboratory, location, deadline,
        contact, score, summary, decision, email, status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(link) DO UPDATE SET
        title = excluded.title,
        description = excluded.description,
        source = excluded.source,
        laboratory = excluded.laboratory,
        location = excluded.location,
        deadline = excluded.deadline,
        contact = excluded.contact,
        score = excluded.score,
        summary = excluded.summary,
        decision = excluded.decision,
        email = COALESCE(NULLIF(offers.email, ''), excluded.email),
        status = offers.status
    """, (
        offer.get("title", ""),
        offer.get("link", ""),
        offer.get("description", ""),
        offer.get("source", ""),
        offer.get("laboratory", ""),
        offer.get("location", ""),
        offer.get("deadline", ""),
        offer.get("contact", ""),
        analysis.get("score"),
        analysis.get("summary", ""),
        analysis.get("decision", "non analysé"),
        offer.get("email", ""),
        normalize_status(offer.get("status")),
    ))

    conn.commit()
    conn.close()


def update_email(link, email_text):
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE offers
    SET email = ?
    WHERE link = ?
    """, (email_text, link))

    conn.commit()
    conn.close()


def update_status(link, status):
    status = normalize_status(status)
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE offers
    SET status = ?
    WHERE link = ?
    """, (status, link))

    conn.commit()
    conn.close()


def cleanup_low_score_offers():
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM offers
    WHERE (
        score < 30
        OR decision = 'ignorer'
    )
    AND status NOT IN ('applied', 'accepted')
    """)

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"[DEBUG] offres faibles nettoyees: {deleted_count}")


def save_offer_without_ai(offer):
    simple_analysis = score_offer_simple(offer)
    score = simple_analysis["score"]
    decision = simple_analysis["decision"]

    if score < 30 and decision not in ("candidater", "a_verifier"):
        print(f"[DEBUG] offre ignoree score faible: {offer.get('title', '')}")
        return False

    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO offers (
        title, link, description, source, laboratory, location, deadline,
        contact, score, summary, decision, email, status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(link) DO UPDATE SET
        title = excluded.title,
        description = excluded.description,
        source = excluded.source,
        laboratory = excluded.laboratory,
        location = excluded.location,
        deadline = excluded.deadline,
        contact = excluded.contact,
        score = excluded.score,
        summary = excluded.summary,
        decision = excluded.decision,
        email = COALESCE(NULLIF(offers.email, ''), excluded.email),
        status = offers.status
    """, (
        offer.get("title", ""),
        offer.get("link", ""),
        offer.get("description", ""),
        offer.get("source", ""),
        offer.get("laboratory", ""),
        offer.get("location", ""),
        offer.get("deadline", ""),
        offer.get("contact", ""),
        score,
        offer.get("summary", ""),
        decision,
        offer.get("email", ""),
        normalize_status(offer.get("status")),
    ))

    conn.commit()
    conn.close()

    return True
