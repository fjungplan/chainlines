import uuid
import psycopg2
from datetime import datetime

DB_HOST = "localhost"
DB_NAME = "cycling_lineage"
DB_USER = "cycling"
DB_PASSWORD = "cycling"
DB_PORT = 5432

SAMPLE_TEAMS = [
    {
        "node_id": uuid.uuid4(),
        "founding_year": 2010,
        "eras": [
            {"year": 2010, "name": "Alpha Cycling", "tier": 1, "uci": "ALP"},
            {"year": 2011, "name": "Alpha Cycling", "tier": 1, "uci": "ALP"},
        ],
    },
    {
        "node_id": uuid.uuid4(),
        "founding_year": 2012,
        "eras": [
            {"year": 2012, "name": "Bravo Pro", "tier": 2, "uci": "BRV"},
            {"year": 2013, "name": "Bravo Pro", "tier": 2, "uci": "BRV"},
        ],
    },
    {
        "node_id": uuid.uuid4(),
        "founding_year": 2014,
        "eras": [
            {"year": 2014, "name": "Charlie Continental", "tier": 3, "uci": "CHA"},
        ],
    },
]


def seed():
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
    )
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM team_node;")
    count = cur.fetchone()[0]
    if count > 1:
        print(f"Existing data detected (team_node count={count}), skipping seed.")
        cur.close()
        conn.close()
        return

    for team in SAMPLE_TEAMS:
        cur.execute(
            """
            INSERT INTO team_node (node_id, founding_year, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
            ON CONFLICT (node_id) DO NOTHING;
            """,
            (str(team["node_id"]), team["founding_year"]),
        )
        for era in team["eras"]:
            era_id = uuid.uuid4()
            cur.execute(
                """
                INSERT INTO team_era (
                    era_id, node_id, season_year, registered_name, uci_code, tier_level,
                    source_origin, is_manual_override, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (era_id) DO NOTHING;
                """,
                (
                    str(era_id),
                    str(team["node_id"]),
                    era["year"],
                    era["name"],
                    era["uci"],
                    era["tier"],
                    "seed_script",
                    True,
                ),
            )
    conn.commit()
    cur.close()
    conn.close()
    print("Seeded sample teams.")


if __name__ == "__main__":
    seed()
