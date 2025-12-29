"""
Seed Audit Log with Sample Pending Edits

This script creates sample EditHistory records with various statuses
to populate the Audit Log UI for testing purposes.

Usage:
    docker compose exec backend python -m app.scripts.seed_audit_log
"""

import uuid
import psycopg2
import os
import random
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse

# --- CONFIGURATION ---
database_url = os.getenv("DATABASE_URL")

if database_url:
    if "+asyncpg" in database_url:
        database_url = database_url.replace("+asyncpg", "")
    url = urlparse(database_url)
    DB_HOST = url.hostname
    DB_NAME = url.path[1:]
    DB_USER = url.username
    DB_PASSWORD = url.password
    DB_PORT = url.port or 5432
else:
    DB_HOST = "localhost"
    DB_NAME = "cycling_lineage"
    DB_USER = "cycling"
    DB_PASSWORD = "cycling"
    DB_PORT = 5432


def seed_audit_log():
    """Create sample EditHistory records for testing the Audit Log UI."""
    print(f"Connecting to database {DB_NAME} on {DB_HOST}...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
        )
        cur = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return

    # Get existing teams to create edits for
    cur.execute("SELECT node_id, legal_name FROM team_node LIMIT 10")
    teams = cur.fetchall()
    
    if not teams:
        print("No teams found. Please run seed_fictional_timeline.py first.")
        cur.close()
        conn.close()
        return

    # Get existing sponsors
    cur.execute("SELECT master_id, legal_name FROM sponsor_master LIMIT 5")
    sponsors = cur.fetchall()

    # Get or create a test user
    cur.execute("SELECT user_id FROM users WHERE email = 'test-seed@example.com' LIMIT 1")
    user_row = cur.fetchone()
    if user_row:
        test_user_id = user_row[0]
    else:
        test_user_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO users (user_id, google_id, email, display_name, role, approved_edits_count, is_banned, created_at)
            VALUES (%s, %s, 'test-seed@example.com', 'Seed Test Editor', 'EDITOR', 0, false, NOW())
            """,
            (test_user_id, f"google-seed-{test_user_id}")
        )
        conn.commit()
        print(f"Created test user with ID: {test_user_id}")

    # Clear existing audit log entries (optional - comment out to keep existing)
    print("Clearing existing audit log entries...")
    cur.execute("DELETE FROM edit_history")
    conn.commit()

    print("Creating sample audit log entries...")
    
    # Sample edit scenarios
    statuses = ['PENDING', 'PENDING', 'PENDING', 'APPROVED', 'REJECTED', 'REVERTED']
    actions = ['UPDATE', 'UPDATE', 'CREATE', 'DELETE']
    entity_types = ['TEAM_NODE', 'TEAM_ERA', 'SPONSOR_MASTER', 'SPONSOR_BRAND', 'LINEAGE_EVENT']
    
    edits_created = 0
    
    # Create edits for teams
    for i, (node_id, legal_name) in enumerate(teams):
        status = random.choice(statuses)
        action = random.choice(actions)
        
        # Create realistic snapshot data
        snapshot_before = {
            "legal_name": legal_name,
            "founding_year": 2000 + i
        }
        snapshot_after = {
            "legal_name": f"{legal_name} (Updated)",
            "founding_year": 2000 + i + 1
        }
        
        edit_id = str(uuid.uuid4())
        created_at = datetime.now() - timedelta(days=random.randint(0, 30))
        
        reviewed_by = None
        reviewed_at = None
        review_notes = None
        
        if status in ['APPROVED', 'REJECTED', 'REVERTED']:
            reviewed_by = test_user_id
            reviewed_at = created_at + timedelta(hours=random.randint(1, 48))
            if status == 'REJECTED':
                review_notes = "Changes do not meet documentation standards"
            elif status == 'REVERTED':
                review_notes = "Reverted due to incorrect data"
        
        cur.execute(
            """
            INSERT INTO edit_history (
                edit_id, entity_type, entity_id, user_id, action, status,
                reviewed_by, reviewed_at, review_notes,
                snapshot_before, snapshot_after, source_notes, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                edit_id, 'team_node', node_id, test_user_id, action, status,
                reviewed_by, reviewed_at, review_notes,
                json.dumps(snapshot_before), json.dumps(snapshot_after),
                f"Sample edit {i+1} for testing",
                created_at
            )
        )
        edits_created += 1

    # Create edits for sponsors
    for i, (master_id, sponsor_name) in enumerate(sponsors):
        status = random.choice(statuses)
        
        snapshot_before = {"legal_name": sponsor_name, "industry_sector": "Technology"}
        snapshot_after = {"legal_name": f"{sponsor_name} Updated", "industry_sector": "Finance"}
        
        edit_id = str(uuid.uuid4())
        created_at = datetime.now() - timedelta(days=random.randint(0, 30))
        
        reviewed_by = None
        reviewed_at = None
        
        if status in ['APPROVED', 'REJECTED']:
            reviewed_by = test_user_id
            reviewed_at = created_at + timedelta(hours=random.randint(1, 48))
        
        cur.execute(
            """
            INSERT INTO edit_history (
                edit_id, entity_type, entity_id, user_id, action, status,
                reviewed_by, reviewed_at,
                snapshot_before, snapshot_after, source_notes, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                edit_id, 'sponsor_master', master_id, test_user_id, 'UPDATE', status,
                reviewed_by, reviewed_at,
                json.dumps(snapshot_before), json.dumps(snapshot_after),
                f"Sample sponsor edit {i+1}",
                created_at
            )
        )
        edits_created += 1

    conn.commit()
    
    # Report results
    cur.execute("SELECT status, COUNT(*) FROM edit_history GROUP BY status")
    status_counts = cur.fetchall()
    
    print(f"\nCreated {edits_created} audit log entries:")
    for status, count in status_counts:
        print(f"  - {status}: {count}")
    
    cur.close()
    conn.close()
    print("\nAudit log seeding complete!")


if __name__ == "__main__":
    seed_audit_log()
