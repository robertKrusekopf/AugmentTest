# Bug Fix: Retired Players Participating in Matches

## Problem Description

**Issue:** Retired players were incorrectly being selected to participate in matches, even though they were correctly excluded from team pages and club pages.

**Symptoms:**
- Retired players appeared under "Kein Team" (No Team) ✓ Correct
- Retired players were NOT shown on their former team's page ✓ Correct  
- Retired players were NOT shown on their former club's page ✓ Correct
- **Retired players were still being selected to play in matches** ✗ BUG

## Root Cause

The player selection logic for match participation had **three locations** where players were queried from the database, but only some of them filtered out retired players:

### Files with the Bug:

1. **`club_player_assignment.py`** - `assign_players_to_teams_for_match_day()` function (line 86-91)
   - Missing `is_retired=False` filter in the ORM query
   
2. **`club_player_assignment.py`** - `batch_assign_players_to_teams()` function (line 369-379)
   - Missing `AND is_retired = 0` filter in the SQL query
   
3. **`auto_lineup.py`** - `create_auto_lineup_for_team()` function (line 151)
   - Missing `is_retired=False` filter in the ORM query

### Files Already Correct:

- **`performance_optimizations.py`** - `batch_set_player_availability()` (line 408) ✓
- **`app.py`** - `/api/matches/<id>/lineup-setup` endpoint (line 2579) ✓
- **`simulation.py`** - `start_new_season()` function (line 3179) ✓

## Solution

Added `is_retired=False` filter to all player queries used for match participation.

### Changes Made:

#### 1. `club_player_assignment.py` - Line 86-91

**Before:**
```python
available_players = Player.query.filter_by(
    club_id=club_id,
    is_available_current_matchday=True,
    has_played_current_matchday=False
).options(
    db.load_only(Player.id, Player.strength, Player.konstanz, Player.drucksicherheit, Player.volle, Player.raeumer)
).all()
```

**After:**
```python
available_players = Player.query.filter_by(
    club_id=club_id,
    is_available_current_matchday=True,
    has_played_current_matchday=False,
    is_retired=False  # ← ADDED
).options(
    db.load_only(Player.id, Player.strength, Player.konstanz, Player.drucksicherheit, Player.volle, Player.raeumer)
).all()
```

#### 2. `club_player_assignment.py` - Line 369-380

**Before:**
```sql
SELECT
    id, name, club_id, strength, konstanz, drucksicherheit, volle, raeumer,
    ausdauer, sicherheit, auswaerts, start, mitte, schluss,
    form_short_term, form_medium_term, form_long_term,
    form_short_remaining_days, form_medium_remaining_days, form_long_remaining_days
FROM player
WHERE club_id IN ({placeholders})
    {player_filter}
ORDER BY club_id, {PLAYER_RATING_SQL} DESC
```

**After:**
```sql
SELECT
    id, name, club_id, strength, konstanz, drucksicherheit, volle, raeumer,
    ausdauer, sicherheit, auswaerts, start, mitte, schluss,
    form_short_term, form_medium_term, form_long_term,
    form_short_remaining_days, form_medium_remaining_days, form_long_remaining_days
FROM player
WHERE club_id IN ({placeholders})
    AND is_retired = 0  -- ← ADDED
    {player_filter}
ORDER BY club_id, {PLAYER_RATING_SQL} DESC
```

#### 3. `auto_lineup.py` - Line 151

**Before:**
```python
# Get all players from the club
club_players = Player.query.filter_by(club_id=team.club_id).all()
```

**After:**
```python
# Get all active (non-retired) players from the club
club_players = Player.query.filter_by(club_id=team.club_id, is_retired=False).all()
```

## Testing Recommendations

To verify the fix works correctly:

1. **Create a test scenario:**
   - Identify a player who is retired (`is_retired=True`)
   - Note which club they belonged to
   - Simulate a match day where that club has a match

2. **Expected behavior after fix:**
   - The retired player should NOT appear in any team lineup
   - The retired player should NOT be selected for match participation
   - Only active players (`is_retired=False`) should be eligible for selection

3. **Verify in database:**
   ```sql
   -- Check retired players
   SELECT id, name, club_id, is_retired, retirement_season_id 
   FROM player 
   WHERE is_retired = 1;
   
   -- Verify they don't appear in any match performances
   SELECT pmp.* 
   FROM player_match_performance pmp
   JOIN player p ON pmp.player_id = p.id
   WHERE p.is_retired = 1
   AND pmp.match_id IN (
       SELECT id FROM match WHERE is_played = 0
   );
   -- Should return 0 rows for future matches
   ```

## Impact

- **Low risk:** The changes only add additional filtering, making queries more restrictive
- **No breaking changes:** Existing functionality remains intact
- **Performance:** Minimal impact - filtering on indexed column (`is_retired`)
- **Consistency:** Now all player selection logic consistently excludes retired players

## Related Files

- `models.py` - Player model with `is_retired` field (line 71)
- `simulation.py` - Retirement logic in `start_new_season()` (line 3186-3202)
- `RETIREMENT_IMPLEMENTATION_SUMMARY.md` - Documentation of retirement system
- `RETIREMENT_MESSAGES.md` - Documentation of retirement notifications

## Date Fixed

2025-10-07

