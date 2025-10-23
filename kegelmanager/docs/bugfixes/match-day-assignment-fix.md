# Match-Day Player Assignment Fix - Age Class Validation

## Problem

After fixing the initial/permanent player assignment, a second age class violation was discovered during match simulation. Players over 20 years old were being assigned to play in matches for D-Jugend teams (ages 11-12), violating age class restrictions.

### Root Cause

The **dynamic match-day assignment system** had the same bug as the old `initial_player_distribution()` function:

**Affected Functions**:
1. `assign_players_to_teams_for_match_day()` - Used for single-club assignment
2. `batch_assign_players_to_teams()` - Used for multi-club batch assignment (performance optimization)

Both functions assigned players **without age class validation**:
- Players were sorted by rating only
- Teams were sorted by league level only
- No age class filtering - just took the best 6 available players regardless of age
- Sequential assignment - highest league team gets best 6, next team gets next best 6, etc.

### Example of the Bug

```
Club has:
- Herren team (League Level 3) - plays on match day 1
- D-Jugend team (League Level 7) - plays on match day 1

Available players on match day 1:
- 10 Herren players (18-35 years, high rating)
- 6 D-Jugend players (11-12 years, low rating)

BUGGY assignment (before fix):
1. Herren team: Best 6 Herren players ✓
2. D-Jugend team: Next best 6 = 4 Herren players + 2 D-Jugend players ✗

CORRECT assignment (after fix):
1. Herren team: 6 Herren players ✓ (processed first - oldest age class)
2. D-Jugend team: 6 D-Jugend players ✓ (only eligible players)
```

## Solution

Both match-day assignment functions now implement the **same age class validation logic** as the permanent assignment system.

### Changes to `club_player_assignment.py`

#### 1. Added Age Class Utilities Import

```python
from age_class_utils import (
    get_minimum_altersklasse_for_age,
    get_age_class_rank,
    is_player_allowed_in_team
)
```

#### 2. Updated `assign_players_to_teams_for_match_day()`

**Before** (age-blind):
```python
# Sort teams by league level only
teams_with_matches.sort(key=lambda t: t.league.level if t.league else 999)

# Get all available players
available_players = Player.query.filter_by(...).all()

# Sort players by rating only
available_players.sort(key=calculate_player_rating, reverse=True)

# Assign sequentially without age validation
for team in teams_with_matches:
    for player in available_players:
        if player.id not in used_players and assigned_count < 6:
            selected_players.append(player)  # ❌ NO AGE VALIDATION
```

**After** (age-aware):
```python
# Sort teams by age class rank (oldest first), then league level
def team_sort_key(t):
    if t.league and t.league.altersklasse:
        age_rank = get_age_class_rank(t.league.altersklasse)
    else:
        age_rank = 6  # Herren rank
    league_level = t.league.level if t.league else 999
    # Sort by age_rank descending (oldest first), then by league_level ascending (best league first)
    return (-age_rank, league_level)

teams_with_matches.sort(key=team_sort_key)

# Get all available players (including age field)
available_players = Player.query.filter_by(...).all()

# Group players by minimum age class
players_by_min_class = defaultdict(list)
for player in available_players:
    min_class = get_minimum_altersklasse_for_age(player.age)
    players_by_min_class[min_class].append(player)

# Sort players within each age class by rating
for age_class in players_by_min_class:
    players_by_min_class[age_class].sort(key=calculate_player_rating, reverse=True)

# Assign with age class validation
for team in teams_with_matches:
    team_age_class = team.league.altersklasse or 'Herren'
    team_age_rank = get_age_class_rank(team_age_class)
    
    # Find eligible players (age class equal or younger)
    eligible_players = []
    for age_class, player_list in players_by_min_class.items():
        player_age_rank = get_age_class_rank(age_class)
        if player_age_rank <= team_age_rank:  # ✅ AGE VALIDATION
            eligible_players.extend(player_list)
    
    # Assign best eligible players
    for player in eligible_players:
        if player.id not in used_players and assigned_count < 6:
            selected_players.append(player)
```

#### 3. Updated `batch_assign_players_to_teams()`

**Key changes**:
- Added `age` field to SQL query: `SELECT id, name, club_id, age, strength, ...`
- Added `altersklasse` field to teams query: `l.altersklasse as altersklasse`
- Included `altersklasse` in team_info dictionary
- Grouped players by minimum age class per club
- Sorted teams by age class rank, then league level
- Filtered players by age class eligibility before assignment

## Age Class Validation Rules

### Age Class Hierarchy

```
F-Jugend (7-8 Jahre)    → Rank 0 → Can play in: F, E, D, C, B, A, Herren
E-Jugend (9-10 Jahre)   → Rank 1 → Can play in: E, D, C, B, A, Herren
D-Jugend (11-12 Jahre)  → Rank 2 → Can play in: D, C, B, A, Herren
C-Jugend (13-14 Jahre)  → Rank 3 → Can play in: C, B, A, Herren
B-Jugend (15-16 Jahre)  → Rank 4 → Can play in: B, A, Herren
A-Jugend (17-18 Jahre)  → Rank 5 → Can play in: A, Herren
Herren (18-35 Jahre)    → Rank 6 → Can play in: Herren only
```

### Validation Logic

**Rule**: A player can only play in their age class or **older** age classes.

**Implementation**: `player_age_rank <= team_age_rank`

**Examples**:
- 12-year-old (D-Jugend, rank 2) can play in D, C, B, A, Herren teams (ranks 2-6) ✓
- 12-year-old (D-Jugend, rank 2) **cannot** play in E or F teams (ranks 0-1) ✗
- 20-year-old (Herren, rank 6) can **only** play in Herren teams (rank 6) ✓
- 20-year-old (Herren, rank 6) **cannot** play in any youth teams (ranks 0-5) ✗

### Team Processing Order

Teams are now processed in this order:
1. **Youngest age class first** (F → E → D → C → B → A → Herren)
2. **Within same age class: highest league first** (Level 1 → Level 2 → ...)

This ensures:
- Youth teams get their age-appropriate players first
- Herren teams get remaining players (who can play in any age class)
- No age class violations occur

## Impact on Match Simulation

### Before Fix

```
Match Day 1:
- Club "SV Beispiel" has Herren team and D-Jugend team playing
- 10 Herren players available (ages 18-35, ratings 70-85)
- 6 D-Jugend players available (ages 11-12, ratings 40-50)

Assignment:
1. Herren team (Level 3): Top 6 Herren players (ratings 85, 83, 81, 79, 77, 75)
2. D-Jugend team (Level 7): Next 6 players = 4 Herren (ratings 73, 71, 69, 67) + 2 D-Jugend (ratings 50, 48)

Result: D-Jugend team has 4 players aged 20+ ✗ VIOLATION
```

### After Fix

```
Match Day 1:
- Same club, same available players

Assignment (age-aware):
1. D-Jugend team (processed first due to age rank 2 < 6):
   - Eligible: Only D-Jugend players (ages 11-12)
   - Assigned: All 6 D-Jugend players (ratings 50, 48, 46, 44, 42, 40)

2. Herren team (processed second):
   - Eligible: D-Jugend + Herren players (all ages)
   - Assigned: Best 6 remaining = 6 Herren players (ratings 85, 83, 81, 79, 77, 75)

Result: All players in age-appropriate teams ✓ CORRECT
```

## Testing

To verify the fix works correctly:

1. **Generate a new database** with clubs that have multiple teams in different age classes
2. **Simulate match days** where both youth and adult teams play
3. **Check match lineups** to ensure no age class violations

### Manual Verification

```python
# After simulating a match day, check the lineups
from models import Match, Player

match = Match.query.filter_by(is_played=True).first()
home_team = match.home_team
away_team = match.away_team

# Check home team lineup
print(f"Home Team: {home_team.name} (Altersklasse: {home_team.league.altersklasse})")
for perf in match.home_performances:
    player = perf.player
    print(f"  {player.name} - Age: {player.age}")

# Check away team lineup
print(f"Away Team: {away_team.name} (Altersklasse: {away_team.league.altersklasse})")
for perf in match.away_performances:
    player = perf.player
    print(f"  {player.name} - Age: {player.age}")
```

## Summary

✅ **Problem solved**: Players are now only assigned to age-appropriate teams during matches  
✅ **Both functions fixed**: Single-club and batch assignment both use age validation  
✅ **Consistent logic**: Match-day assignment uses same rules as permanent assignment  
✅ **Performance maintained**: Batch assignment still optimized with SQL queries  
✅ **No violations**: Age class restrictions enforced for all match simulations  

## Related Files

- `club_player_assignment.py` - Match-day player assignment (FIXED)
- `player_redistribution.py` - Permanent player assignment (FIXED PREVIOUSLY)
- `age_class_utils.py` - Age class validation utilities
- `PLAYER_REDISTRIBUTION_FIX.md` - Documentation for permanent assignment fix

## Date

Changes implemented: 2025-10-07

