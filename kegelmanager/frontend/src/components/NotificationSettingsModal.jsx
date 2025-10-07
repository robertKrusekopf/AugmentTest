import { useState, useEffect } from 'react';
import { getNotificationSettings, updateNotificationSettings, getNotificationCategories } from '../services/api';
import './NotificationSettingsModal.css';

const NotificationSettingsModal = ({ isOpen, onClose, onSave }) => {
  const [settings, setSettings] = useState({});
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [settingsData, categoriesData] = await Promise.all([
        getNotificationSettings(),
        getNotificationCategories()
      ]);
      
      setSettings(settingsData);
      setCategories(categoriesData);
      setLoading(false);
    } catch (err) {
      console.error('Error loading notification settings:', err);
      setError('Fehler beim Laden der Einstellungen');
      setLoading(false);
    }
  };

  const handleToggle = (categoryId) => {
    setSettings(prev => ({
      ...prev,
      [categoryId]: !prev[categoryId]
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage('');
      
      await updateNotificationSettings(settings);
      
      setSuccessMessage('Einstellungen erfolgreich gespeichert!');
      setSaving(false);
      
      // Call onSave callback if provided
      if (onSave) {
        onSave();
      }
      
      // Close modal after a short delay
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err) {
      console.error('Error saving notification settings:', err);
      setError('Fehler beim Speichern der Einstellungen');
      setSaving(false);
    }
  };

  const handleSelectAll = () => {
    const allEnabled = {};
    categories.forEach(category => {
      allEnabled[category.id] = true;
    });
    setSettings(prev => ({ ...prev, ...allEnabled }));
  };

  const handleDeselectAll = () => {
    const allDisabled = {};
    categories.forEach(category => {
      allDisabled[category.id] = false;
    });
    setSettings(prev => ({ ...prev, ...allDisabled }));
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content notification-settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Benachrichtigungseinstellungen</h2>
          <button className="modal-close" onClick={onClose}>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="loading">Laden...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : (
            <>
              <p className="settings-description">
                Wählen Sie aus, welche Arten von Benachrichtigungen Sie erhalten möchten.
                Deaktivierte Benachrichtigungen werden nicht in Ihrer Nachrichtenliste angezeigt.
              </p>

              <div className="settings-actions">
                <button className="btn btn-secondary btn-sm" onClick={handleSelectAll}>
                  Alle auswählen
                </button>
                <button className="btn btn-secondary btn-sm" onClick={handleDeselectAll}>
                  Alle abwählen
                </button>
              </div>

              <div className="notification-categories">
                {categories.map(category => (
                  <div key={category.id} className="category-item">
                    <label className="category-label">
                      <input
                        type="checkbox"
                        checked={settings[category.id] || false}
                        onChange={() => handleToggle(category.id)}
                      />
                      <div className="category-info">
                        <div className="category-name">{category.name}</div>
                        <div className="category-description">{category.description}</div>
                      </div>
                    </label>
                  </div>
                ))}
              </div>

              {successMessage && (
                <div className="success-message">{successMessage}</div>
              )}
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose} disabled={saving}>
            Abbrechen
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving || loading}>
            {saving ? 'Speichern...' : 'Speichern'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettingsModal;

