# Nationality Feature Setup Guide

## Overview

The nationality feature adds a "Nationalität" field to all players in the bowling simulation game. By default, all players are set to "Deutsch" (German) with a German flag icon 🇩🇪.

## Features

✅ **Database Integration**: Nationality stored in Player model  
✅ **Default Value**: All players default to "Deutsch"  
✅ **Visual Display**: German flag icon in player profiles  
✅ **Cheat Mode**: Edit nationality in cheat mode  
✅ **Migration Support**: Safe migration for existing databases  
✅ **API Integration**: Nationality included in all player API responses  

## Installation

### For New Databases
No action required! The nationality feature is automatically included when creating new databases.

### For Existing Databases

#### Step 1: Create Backup
**IMPORTANT**: Always create a backup before migration!

```bash
# Windows
copy kegelmanager\backend\instance\your_database.db kegelmanager\backend\instance\your_database_backup.db

# Linux/Mac
cp kegelmanager/backend/instance/your_database.db kegelmanager/backend/instance/your_database_backup.db
```

#### Step 2: Run Migration
```bash
cd kegelmanager/backend
python migrate_add_nationality.py
```

The script will:
- ✅ Add `nationalitaet` column to Player table
- ✅ Set nationality to 'Deutsch' for all existing players
- ✅ Create automatic backups
- ✅ Work with multiple databases
- ✅ Safe to run multiple times

#### Step 3: Restart Application
```bash
# Backend
cd kegelmanager/backend
python app.py

# Frontend (in new terminal)
cd kegelmanager/frontend
npm start
```

## Usage

### Viewing Player Nationality
1. Navigate to any player's detail page
2. Nationality is displayed:
   - In the player header with flag icon 🇩🇪
   - In the "Persönliche Daten" section

### Editing Player Nationality (Cheat Mode)
1. Enable cheat mode in settings
2. Go to player detail page
3. Click "Cheat" tab
4. Edit the "Nationalität" field
5. Save changes

## Technical Details

### Database Schema
```sql
ALTER TABLE player ADD COLUMN nationalitaet VARCHAR(50) DEFAULT 'Deutsch' NOT NULL;
```

### API Response
Player objects now include:
```json
{
  "id": 1,
  "name": "Max Mustermann",
  "nationalitaet": "Deutsch",
  ...
}
```

### Files Modified
- `backend/models.py` - Player model
- `backend/app.py` - API endpoints
- `backend/init_db.py` - Player generation
- `backend/extend_existing_db.py` - Player generation
- `frontend/src/pages/PlayerDetail.jsx` - UI display
- `frontend/src/pages/PlayerDetail.css` - Styling

### New Files
- `backend/migrate_add_nationality.py` - Migration script

## Troubleshooting

### Migration Fails
1. Close the application completely
2. Check file permissions
3. Restore from backup
4. Try migration again

### Nationality Not Showing
1. Clear browser cache
2. Restart frontend development server
3. Check browser console for errors

### Database Errors
1. Ensure database is not in use
2. Check SQLite file permissions
3. Verify backup exists before retrying

## Future Enhancements

Possible future improvements:
- Multiple nationality support
- Flag icons for other countries
- Nationality-based player generation
- Import/export nationality data
- Nationality statistics and filtering

## Support

If you encounter issues:
1. Check the migration script output for errors
2. Verify all files were modified correctly
3. Ensure database backups are available
4. Test with a fresh database if needed
