import React from 'react';
import LineupSelector from './LineupSelector';

// Simple test component to verify the LineupSelector renders without errors
const LineupSelectorTest = () => {
  const handleSave = () => {
    console.log('Save clicked');
  };

  const handleCancel = () => {
    console.log('Cancel clicked');
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>LineupSelector Test</h1>
      <LineupSelector
        matchId={1}
        managedClubId={1}
        onSave={handleSave}
        onCancel={handleCancel}
      />
    </div>
  );
};

export default LineupSelectorTest;
