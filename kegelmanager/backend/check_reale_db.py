import sqlite3

# Check original database
print("=== Original RealeDB.db ===")
conn = sqlite3.connect('instance/RealeDB.db')
cursor = conn.cursor()

# Check cups
cursor.execute('SELECT COUNT(*) FROM cup')
cup_count = cursor.fetchone()[0]
print(f'Cups in RealeDB.db: {cup_count}')

# Check leagues with bundesland/landkreis
cursor.execute('SELECT DISTINCT bundesland FROM league WHERE bundesland IS NOT NULL AND bundesland != ""')
bundeslaender = cursor.fetchall()
print(f'Bundeslaender: {len(bundeslaender)} - {[b[0] for b in bundeslaender[:5]]}')

cursor.execute('SELECT DISTINCT landkreis FROM league WHERE landkreis IS NOT NULL AND landkreis != ""')
landkreise = cursor.fetchall()
print(f'Landkreise: {len(landkreise)} - {[l[0] for l in landkreise[:5]]}')

conn.close()

# Check extended database
print("\n=== Extended RealeDB_with_cups_fixed.db ===")
conn = sqlite3.connect('instance/RealeDB_with_cups_fixed.db')
cursor = conn.cursor()

# Check cups
cursor.execute('SELECT COUNT(*) FROM cup')
cup_count = cursor.fetchone()[0]
print(f'Cups in RealeDB_with_cups_fixed.db: {cup_count}')

if cup_count > 0:
    cursor.execute('SELECT id, name, cup_type, season_id FROM cup')
    cups = cursor.fetchall()
    print("Created cups:")
    for cup in cups:
        print(f"  ID {cup[0]}: {cup[1]} ({cup[2]}) - Season {cup[3]}")

# Check cup matches
cursor.execute('SELECT COUNT(*) FROM cup_match')
cup_match_count = cursor.fetchone()[0]
print(f'Cup matches: {cup_match_count}')

# Check if cup matches have dates
cursor.execute('SELECT COUNT(*) FROM cup_match WHERE match_date IS NOT NULL')
cup_matches_with_dates = cursor.fetchone()[0]
print(f'Cup matches with dates: {cup_matches_with_dates}')

# Check season calendar for cup days
cursor.execute('SELECT COUNT(*) FROM season_calendar WHERE day_type = "CUP_DAY"')
cup_days_count = cursor.fetchone()[0]
print(f'CUP_DAYs in calendar: {cup_days_count}')

conn.close()
