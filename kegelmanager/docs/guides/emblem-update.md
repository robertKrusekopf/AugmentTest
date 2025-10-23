# Quick Guide: Updating Components to Use ClubEmblem

This guide provides step-by-step instructions for updating each remaining component to use the new `ClubEmblem` component.

## General Pattern

### 1. Add Import
```jsx
import ClubEmblem from '../components/ClubEmblem';
```

### 2. Replace Image Tag
**Before:**
```jsx
{club.emblem_url ? (
  <img
    src={club.emblem_url}
    alt={`${club.name} Wappen`}
    className="club-emblem"
    onError={(e) => {
      e.target.style.display = 'none';
      e.target.parentNode.innerHTML = `<span>...</span>`;
    }}
  />
) : (
  <span>...</span>
)}
```

**After:**
```jsx
<ClubEmblem
  emblemUrl={club.emblem_url}
  clubName={club.name}
  className="club-emblem"
/>
```

## Component-Specific Instructions

### 1. ClubDetail.jsx

**Locations to update:**
- Line ~195-208: Club header emblem
- Line ~288-301: Team list emblems (in overview tab)
- Line ~399-412: Team cards emblems (in teams tab)

**Example for club header:**
```jsx
// Add import at top
import ClubEmblem from '../components/ClubEmblem';

// Replace lines 195-208
<div className="club-logo">
  <ClubEmblem
    emblemUrl={club.emblem_url}
    clubName={club.name}
    className="club-emblem"
  />
</div>
```

### 2. TeamDetail.jsx

**Locations to update:**
- Line ~214-227: Team header emblem
- Line ~1486-1493: Cup history elimination emblems

**Example for team header:**
```jsx
// Add import at top
import ClubEmblem from '../components/ClubEmblem';

// Replace lines 214-227
<div className="team-logo">
  <ClubEmblem
    emblemUrl={team.club?.emblem_url}
    clubName={team.club?.name || team.name}
    className="club-emblem"
  />
</div>
```

### 3. Teams.jsx

**Locations to update:**
- Line ~142-155: Team card emblems

**Example:**
```jsx
// Add import at top
import ClubEmblem from '../components/ClubEmblem';

// Replace lines 142-155
<div className="team-logo">
  <ClubEmblem
    emblemUrl={team.emblemUrl}
    clubName={team.club}
    className="club-emblem"
  />
</div>
```

### 4. LeagueDetail.jsx

**Locations to update:**
- Line ~451-464: Teams tab emblems
- Line ~535-542: Standings table emblems

**Example for teams tab:**
```jsx
// Add import at top
import ClubEmblem from '../components/ClubEmblem';

// Replace lines 451-464
<div className="team-logo">
  <ClubEmblem
    emblemUrl={team.emblem_url}
    clubName={team.name}
    className="club-emblem"
  />
</div>
```

**Example for standings table:**
```jsx
// Replace lines 535-542
<div className="club-row-info">
  <ClubEmblem
    emblemUrl={team.emblem_url}
    clubName={team.team_name}
    className="club-emblem-small"
  />
  <Link to={`/teams/${team.team_id}`}>{team.team_name}</Link>
</div>
```

### 5. Leagues.jsx

**Locations to update:**
- Line ~520-533: Teams tab emblems

**Example:**
```jsx
// Add import at top
import ClubEmblem from '../components/ClubEmblem';

// Replace lines 520-533
<div className="team-logo">
  <ClubEmblem
    emblemUrl={team.emblem_url}
    clubName={team.name}
    className="club-emblem"
  />
</div>
```

### 6. CupsOverview.jsx

**Locations to update:**
- Line ~430-438: Eligible teams emblems

**Example:**
```jsx
// Add import at top
import ClubEmblem from '../components/ClubEmblem';

// Replace lines 430-438
<div className="team-header">
  <ClubEmblem
    emblemUrl={team.emblem_url}
    clubName={team.club_name}
    className="team-emblem"
  />
  <h3>{team.name}</h3>
</div>
```

### 7. MatchDetail.jsx

**Locations to update:**
- Line ~181-186: Home team emblem
- Line ~193-198: Away team emblem (similar pattern)

**Example:**
```jsx
// Add import at top
import ClubEmblem from '../components/ClubEmblem';

// Replace lines 181-186
<Link to={`/teams/${match.home_team_id}`} className="team-logo">
  <ClubEmblem
    emblemUrl={`/api/club-emblem/${match.home_team_verein_id || match.home_team_club_id}`}
    clubName={match.home_team_name}
    className="team-emblem"
  />
</Link>
```

## Testing After Each Update

After updating each component:

1. **Navigate to the page** in your browser
2. **Check emblems load** without flickering
3. **Verify fallbacks** appear for missing emblems
4. **Test error cases** by temporarily breaking an emblem URL
5. **Check browser console** for any errors

## Common Issues and Solutions

### Issue: Emblem not showing at all
**Solution:** Check that `emblemUrl` prop is being passed correctly. Use browser DevTools to inspect the component.

### Issue: Fallback not showing
**Solution:** Ensure `clubName` prop is provided. The component requires this prop.

### Issue: Wrong size
**Solution:** Check the `className` prop matches the CSS class you want (e.g., `club-emblem`, `club-emblem-small`, `team-emblem`).

### Issue: Still seeing flickering
**Solution:** Make sure you've removed the old `<img>` tag completely and aren't mixing old and new patterns.

## Verification Checklist

After updating all components, verify:

- [ ] No console errors related to emblems
- [ ] No flickering during page loads
- [ ] Fallback initials display correctly
- [ ] All emblem sizes render correctly
- [ ] Lazy loading works (check Network tab)
- [ ] Cache headers are being used (check Network tab)
- [ ] No broken image icons appear

## Need Help?

If you encounter issues:
1. Check the browser console for errors
2. Inspect the component in React DevTools
3. Verify the emblem URL is correct in the Network tab
4. Compare your code with the examples in this guide
5. Refer to `EMBLEM_DISPLAY_FIX.md` for detailed implementation notes

