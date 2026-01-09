import asyncio
from app.db.database import async_session_maker
from sqlalchemy import text

async def check_prominence():
    async with async_session_maker() as session:
        # Check Team Polti VisitMalta 2025
        query = text("""
            SELECT 
                te.registered_name,
                te.season_year,
                sb.brand_name,
                tsl.prominence_percent,
                tsl.rank_order,
                sm.legal_name as master_name
            FROM team_era te
            JOIN team_sponsor_link tsl ON te.era_id = tsl.era_id
            JOIN sponsor_brand sb ON tsl.brand_id = sb.brand_id
            JOIN sponsor_master sm ON sb.master_id = sm.master_id
            WHERE te.registered_name LIKE '%Polti%' AND te.season_year = 2025
            ORDER BY tsl.rank_order
        """)
        result = await session.execute(query)
        rows = result.fetchall()
        
        print("\n=== Team Polti VisitMalta 2025 ===")
        title_total = 0
        for r in rows:
            print(f"  {r[2]}: {r[3]}% (rank {r[4]}) - Master: {r[5]}")
            if r[4] <= 2:  # Assuming first 2 are title sponsors
                title_total += r[3]
        print(f"  Title sponsor total: {title_total}%\n")
        
        # Check Cofidis 2025
        query2 = text("""
            SELECT 
                te.registered_name,
                te.season_year,
                sb.brand_name,
                tsl.prominence_percent,
                tsl.rank_order
            FROM team_era te
            JOIN team_sponsor_link tsl ON te.era_id = tsl.era_id
            JOIN sponsor_brand sb ON tsl.brand_id = sb.brand_id
            WHERE te.registered_name LIKE '%Cofidis%' AND te.season_year = 2025
            ORDER BY tsl.rank_order
        """)
        result2 = await session.execute(query2)
        rows2 = result2.fetchall()
        
        print("=== Cofidis 2025 ===")
        title_total2 = 0
        for r in rows2:
            print(f"  {r[2]}: {r[3]}% (rank {r[4]})")
            if r[4] == 1:  # First sponsor
                title_total2 += r[3]
        print(f"  Title sponsor total: {title_total2}%\n")

asyncio.run(check_prominence())
