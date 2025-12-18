
import uuid
import psycopg2
import os
import random
from datetime import date, datetime, timedelta
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

# --- DATA GENERATORS ---

SPONSORS_DATA = [
    # (Master Name, Industry, [Brand Name, HexColor])
    ("Global Tech Solutions", "Technology", [("CloudSys", "#3498db"), ("DataFlow", "#2980b9")]),
    ("Oceanic Beverages", "Beverages", [("Fizz", "#e74c3c"), ("HydroPure", "#34495e")]),
    ("Apex Automotive", "Automotive", [("Veloce Motors", "#e67e22"), ("Apex Trucks", "#d35400")]),
    ("National Banking Grp", "Finance", [("NBG Bank", "#2c3e50"), ("NBG Insurance", "#27ae60")]),
    ("Telekom Giant", "Telecommunications", [("Connect", "#8e44ad"), ("FibreNet", "#9b59b6")]),
    ("Retail King", "Retail", [("SuperMart", "#f1c40f"), ("MegaStore", "#f39c12")]),
    ("Energy Plus", "Energy", [("PowerGrid", "#c0392b"), ("Solaris", "#d35400")]),
    ("Insurance Co", "Insurance", [("SecureLife", "#1abc9c"), ("SafeGuard", "#16a085")]),
    ("Floor Masters", "Home Improvement", [("QuickFloor", "#95a5a6")]),
    ("Lotto Nation", "Gambling", [("LottoPot", "#c0392b")]),
    ("Construct Corp", "Construction", [("BuildIt", "#7f8c8d")]),
    ("Airline One", "Transport", [("AirOne", "#2980b9")]),
    ("Bike Maker X", "Sports Equipment", [("Velox Bikes", "#2ecc71")]),
    ("Tourism Board Y", "Tourism", [("Visit Country Y", "#f1c40f")]),
    ("PetroChem", "Chemicals", [("ChemCo", "#8e44ad")]),
    ("Logistics Int", "Logistics", [("SpeedPostal", "#e74c3c")]),
    ("Coffee Roasters", "Food & Beverage", [("BeanCafe", "#6f4e37")]),
    ("Betting World", "Gambling", [("BetWin", "#27ae60")]),
    ("Software House", "Technology", [("SoftSol", "#2980b9")]),
]

TIERS = [1, 1, 1, 2, 2, 3] # Weighted towards Pro/WT for main teams


COUNTRIES = ['FRA', 'ITA', 'BEL', 'ESP', 'USA', 'GBR', 'GER', 'NED', 'AUS', 'COL']

def get_random_date(year):
    """Returns Jan 1st of the year."""
    return date(year, 1, 1)

def seed():
    print(f"Connecting to database {DB_NAME} on {DB_HOST}...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
        )
        cur = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return

    # 1. Clear Data
    print("Clearing existing data...")
    tables = ["lineage_event", "team_sponsor_link", "team_era", "team_node", "sponsor_brand", "sponsor_master"]
    for table in tables:
        cur.execute(f"DELETE FROM {table};")
    conn.commit()
    print("Clean slate prepared.")

    # 2. Create Sponsors
    print("Seeding Sponsors...")
    brands_pool = [] # List of {id, name, color}
    
    for m_name, sector, brands in SPONSORS_DATA:
        master_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO sponsor_master (master_id, legal_name, display_name, industry_sector, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            """,
            (master_id, m_name, m_name, sector)
        )
        
        for b_name, color in brands:
            brand_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO sponsor_brand (brand_id, master_id, brand_name, display_name, default_hex_color, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """,
                (brand_id, master_id, b_name, b_name, color)
            )
            brands_pool.append({"id": brand_id, "name": b_name, "color": color})
            
    conn.commit()
    print(f"Seeded {len(SPONSORS_DATA)} masters and {len(brands_pool)} brands.")

    # 3. Create Teams and Scenarios
    print("Seeding Teams & Lineage...")
    
    # Track node IDs for lineage
    team_nodes = {} # key -> uuid


    # Global tracker for sponsor exclusivity: set of (brand_id, year)
    sponsor_usage_registry = set()

    def get_available_brands(year, exclude_ids=[]):
        """Return list of brands not currently sponsoring any team in the given year."""
        available = []
        for b in brands_pool:
            if b['id'] in exclude_ids:
                continue
            if (b['id'], year) not in sponsor_usage_registry:
                available.append(b)
        return available

    # Helper to generate eras for a team
    def create_team_history(key, name_base, start_year, end_year=2025, stable_sponsors=False, country_code=None):
        node_id = str(uuid.uuid4())
        team_nodes[key] = node_id
        
        # Pick country if not provided -> Stable lifetime country
        if not country_code:
            country_code = random.choice(COUNTRIES)

        # Create Node
        cur.execute(
            """
            INSERT INTO team_node (node_id, legal_name, founding_year, dissolution_year, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            """,
            (node_id, f"{name_base} Legal Entity", start_year, end_year if end_year < 2025 else None)
        )

        current_year = start_year
        
        # State for sponsors: { 'brand': dict, 'contract_end': int }
        # Initialize with None
        s1_state = {'brand': None, 'contract_end': -1}
        s2_state = {'brand': None, 'contract_end': -1}
        s3_state = {'brand': None, 'contract_end': -1}
        s4_state = {'brand': None, 'contract_end': -1}
        
        last_reg_name = None

        while current_year <= end_year:
            # 1. Manage Sponsor 1
            if s1_state['brand'] is None or current_year > s1_state['contract_end']:
                # Need a new main sponsor
                exclude = [s['brand']['id'] for s in [s2_state, s3_state, s4_state] if s['brand']]
                potential_brands = get_available_brands(current_year, exclude_ids=exclude)
                
                # Promotion Check (S2 -> S1)
                promoted = False
                if s2_state['brand'] and random.random() < 0.3: 
                     s1_state['brand'] = s2_state['brand']
                     s2_state['brand'] = None
                     s2_state['contract_end'] = -1
                     promoted = True
                
                if not promoted:
                    if not potential_brands:
                        print(f"WARN: No brands available for {key} in {current_year}!")
                        break 
                    s1_state['brand'] = random.choice(potential_brands)
                
                if stable_sponsors:
                    duration = random.choice([4, 5, 6, 7, 8])
                else:
                    duration = random.choices([2, 3, 4, 5, 8], weights=[20, 30, 30, 15, 5])[0]
                s1_state['contract_end'] = current_year + duration - 1

            # 2. Manage Sponsor 2 (80% chance if empty)
            if s2_state['brand'] is None or current_year > s2_state['contract_end']:
                if random.random() < 0.8:
                    exclude = [s['brand']['id'] for s in [s1_state, s3_state, s4_state] if s['brand']]
                    potential_brands = get_available_brands(current_year, exclude_ids=exclude)
                    if potential_brands:
                         s2_state['brand'] = random.choice(potential_brands)
                         duration = random.choices([1, 2, 3], weights=[30, 50, 20])[0]
                         s2_state['contract_end'] = current_year + duration - 1
                else:
                    s2_state['brand'] = None

            # 3. Manage Sponsor 3 (40% chance if empty)
            if s3_state['brand'] is None or current_year > s3_state['contract_end']:
                if random.random() < 0.4:
                    exclude = [s['brand']['id'] for s in [s1_state, s2_state, s4_state] if s['brand']]
                    potential_brands = get_available_brands(current_year, exclude_ids=exclude)
                    if potential_brands:
                         s3_state['brand'] = random.choice(potential_brands)
                         duration = random.choices([1, 2], weights=[60, 40])[0]
                         s3_state['contract_end'] = current_year + duration - 1
                else:
                    s3_state['brand'] = None

            # 4. Manage Sponsor 4 (20% chance if S3 exists and empty)
            if s4_state['brand'] is None or current_year > s4_state['contract_end']:
                if s3_state['brand'] and random.random() < 0.2:
                    exclude = [s['brand']['id'] for s in [s1_state, s2_state, s3_state] if s['brand']]
                    potential_brands = get_available_brands(current_year, exclude_ids=exclude)
                    if potential_brands:
                         s4_state['brand'] = random.choice(potential_brands)
                         duration = 1
                         s4_state['contract_end'] = current_year + duration - 1
                else:
                    s4_state['brand'] = None

            # Register Usage
            for s in [s1_state, s2_state, s3_state, s4_state]:
                if s['brand']: sponsor_usage_registry.add((s['brand']['id'], current_year))
                
            # 3. Attributes for Era
            tier = random.choice(TIERS)
            
            # Naming Convention
            # If S1 is new this year, or name change forced:
            if s2_state['brand']:
                 reg_name = f"{s1_state['brand']['name']} - {s2_state['brand']['name']}"
            else:
                 reg_name = f"{s1_state['brand']['name']} Pro Cycling"
            
            uci_code = (s1_state['brand']['name'][:3]).upper()
            
            era_id = str(uuid.uuid4())
            valid_from = date(current_year, 1, 1)
            
            cur.execute(
                """
                INSERT INTO team_era (
                    era_id, node_id, season_year, valid_from, registered_name, uci_code, country_code, tier_level, 
                    is_manual_override, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """,
                (era_id, node_id, current_year, valid_from, reg_name, uci_code, country_code, tier, False)
            )
            
            # Links & Prominence Calculation
            active_sponsors = []
            if s1_state['brand']: active_sponsors.append({'state': s1_state, 'rank': 1})
            if s2_state['brand']: active_sponsors.append({'state': s2_state, 'rank': 2})
            if s3_state['brand']: active_sponsors.append({'state': s3_state, 'rank': 3})
            if s4_state['brand']: active_sponsors.append({'state': s4_state, 'rank': 4})
            
            count = len(active_sponsors)
            prominences = []
            
            if count == 1:
                prominences = [100]
            elif count == 2:
                # S1: 51-70% (User req: max 70)
                p1 = random.randint(51, 70)
                prominences = [p1, 100 - p1]
            elif count == 3:
                # S1: 45-60% (User req: max 60)
                p1 = random.randint(45, 60)
                remainder = 100 - p1
                # Split remainder between 2 roughly equally (~20-27%)
                s2 = (remainder // 2) + random.randint(-2, 2)
                s3 = remainder - s2
                prominences = [p1, s2, s3]
            elif count >= 4:
                # S1: 30-40% (User req: max 40)
                # Ensure S1 is biggest: 30 > (70/3=23), safe.
                p1 = random.randint(30, 40)
                remainder = 100 - p1
                others_count = count - 1
                base_other = remainder // others_count
                
                others = []
                for _ in range(others_count - 1):
                    val = base_other + random.randint(-2, 2)
                    others.append(val)
                others.append(remainder - sum(others))
                others.sort(reverse=True)
                prominences = [p1] + others

            # Write to DB
            for idx, item in enumerate(active_sponsors):
                brand = item['state']['brand']
                rank = item['rank']
                prom = prominences[idx]
                
                cur.execute(
                    """
                    INSERT INTO team_sponsor_link (
                        link_id, era_id, brand_id, rank_order, prominence_percent, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (str(uuid.uuid4()), era_id, brand['id'], rank, prom)
                )
            
            current_year += 1

            
    # SCENARIOS
    
    # 1. Stable Long Runner
    create_team_history("team_A", "Team Alpha", 2000, 2025, stable_sponsors=False, country_code="FRA")
    
    # 2. The Merger: B + C -> BC
    create_team_history("team_B", "Blue Riders", 2005, 2014, stable_sponsors=True, country_code="BEL")
    create_team_history("team_C", "Crimson Velo", 2008, 2014, stable_sponsors=True, country_code="BEL")
    create_team_history("team_BC", "Purple Fusion", 2015, 2025, stable_sponsors=False, country_code="BEL")
    
    # 3. The Split: D -> D1, D2
    create_team_history("team_D", "Delta Force", 2000, 2010, country_code="ITA")
    create_team_history("team_D1", "Delta One", 2011, 2025, country_code="ITA")
    create_team_history("team_D2", "Delta Two", 2011, 2018, country_code="ITA") # Folded later
    
    # 4. License Transfer: E -> F
    create_team_history("team_E", "Echo Base", 2002, 2008, country_code="ESP")
    create_team_history("team_F", "Foxtrot Flyers", 2009, 2025, country_code="RUS") # Flag change!
    
    # 5. Complex Chain: G -> H -> I
    create_team_history("team_G", "Golf Club", 1995, 2005, country_code="USA")
    create_team_history("team_H", "Hotel Lobby", 2006, 2012, country_code="USA")
    create_team_history("team_I", "India Ink", 2013, 2025, country_code="USA")
    
    # 6. Filler Teams (Stable)
    for i in range(10):
        start_y = random.randint(2000, 2015)
        create_team_history(f"filler_{i}", f"Team {i}", start_y, 2025)

    conn.commit()
    print("Teams created.")

    # 4. Create Lineage Events
    print("Linking Lineage...")
    
    events = [
        # Merge B+C -> BC
        (team_nodes["team_B"], team_nodes["team_BC"], 2015, "MERGE", "Team B merged into Team BC"),
        (team_nodes["team_C"], team_nodes["team_BC"], 2015, "MERGE", "Team C merged into Team BC"),
        
        # Split D -> D1, D2
        (team_nodes["team_D"], team_nodes["team_D1"], 2011, "SPLIT", "Team D split into D1"),
        (team_nodes["team_D"], team_nodes["team_D2"], 2011, "SPLIT", "Team D split into D2"),
        
        # Transfer E -> F
        (team_nodes["team_E"], team_nodes["team_F"], 2009, "LEGAL_TRANSFER", "License transferred from E to F"),
        
        # Chain G->H->I
        (team_nodes["team_G"], team_nodes["team_H"], 2006, "SPIRITUAL_SUCCESSION", "Rebrand G to H"),
        (team_nodes["team_H"], team_nodes["team_I"], 2013, "LEGAL_TRANSFER", "Owner changed H to I"),
    ]
    
    for pred, succ, year, type, note in events:
        cur.execute(
            """
            INSERT INTO lineage_event (
                event_id, predecessor_node_id, successor_node_id, event_year, event_type, notes, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (str(uuid.uuid4()), pred, succ, year, type, note)
        )
        
    conn.commit()
    
    cur.close()
    conn.close()
    print("Seeding Complete!")

if __name__ == "__main__":
    seed()
