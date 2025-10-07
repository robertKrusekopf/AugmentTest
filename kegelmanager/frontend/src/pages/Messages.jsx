import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMessages, getMessage, markMessageRead, markMessageUnread, deleteMessage, markAllMessagesRead } from '../services/api';
import NotificationSettingsModal from '../components/NotificationSettingsModal';
import './Messages.css';

const Messages = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all', 'unread', 'read'
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // Load messages on component mount
  useEffect(() => {
    loadMessages();
  }, [filter]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      setError(null);

      let messagesData;
      if (filter === 'unread') {
        messagesData = await getMessages(false);
      } else if (filter === 'read') {
        messagesData = await getMessages(true);
      } else {
        messagesData = await getMessages();
      }

      setMessages(messagesData);

      // If a message was selected, reload it to get updated data
      if (selectedMessage) {
        const updatedMessage = messagesData.find(m => m.id === selectedMessage.id);
        if (updatedMessage) {
          setSelectedMessage(updatedMessage);
        } else {
          setSelectedMessage(null);
        }
      }

      setLoading(false);

      // Trigger event to update sidebar
      window.dispatchEvent(new Event('messagesUpdated'));
    } catch (err) {
      console.error('Error loading messages:', err);
      setError('Fehler beim Laden der Nachrichten');
      setLoading(false);
    }
  };

  const handleSelectMessage = async (message) => {
    try {
      // Load full message details
      const fullMessage = await getMessage(message.id);
      setSelectedMessage(fullMessage);
      
      // Mark as read if it was unread
      if (!message.is_read) {
        await markMessageRead(message.id);
        loadMessages(); // Reload to update the list
      }
    } catch (err) {
      console.error('Error selecting message:', err);
    }
  };

  const handleToggleRead = async (messageId, currentReadStatus) => {
    try {
      if (currentReadStatus) {
        await markMessageUnread(messageId);
      } else {
        await markMessageRead(messageId);
      }
      loadMessages();
    } catch (err) {
      console.error('Error toggling read status:', err);
    }
  };

  const handleDeleteMessage = async (messageId) => {
    if (!window.confirm('Möchten Sie diese Nachricht wirklich löschen?')) {
      return;
    }
    
    try {
      await deleteMessage(messageId);
      
      // Clear selection if the deleted message was selected
      if (selectedMessage && selectedMessage.id === messageId) {
        setSelectedMessage(null);
      }
      
      loadMessages();
    } catch (err) {
      console.error('Error deleting message:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllMessagesRead();
      loadMessages();
    } catch (err) {
      console.error('Error marking all messages as read:', err);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Gerade eben';
    if (diffMins < 60) return `vor ${diffMins} Min.`;
    if (diffHours < 24) return `vor ${diffHours} Std.`;
    if (diffDays < 7) return `vor ${diffDays} Tag${diffDays > 1 ? 'en' : ''}`;

    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Render message content with clickable links
  const renderMessageContent = (content) => {
    // Convert newlines to <br> tags
    const contentWithBreaks = content.replace(/\n/g, '<br>');

    return (
      <div
        className="message-content-html"
        dangerouslySetInnerHTML={{ __html: contentWithBreaks }}
        onClick={handleContentClick}
      />
    );
  };

  // Handle clicks on links in message content
  const handleContentClick = (e) => {
    // Check if the clicked element is a link
    if (e.target.tagName === 'A') {
      e.preventDefault();
      const href = e.target.getAttribute('href');

      // Navigate to the link if it's an internal link
      if (href && href.startsWith('/')) {
        navigate(href);
      } else if (href && href.startsWith('http')) {
        // Open external links in a new tab
        window.open(href, '_blank');
      }
    }
  };

  const getMessageTypeIcon = (type) => {
    switch (type) {
      case 'success':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
        );
      case 'warning':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
        );
      case 'error':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
        );
      default:
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
        );
    }
  };

  const unreadCount = messages.filter(m => !m.is_read).length;

  return (
    <div className="messages-page">
      <div className="messages-header">
        <h1 className="page-title">Nachrichten</h1>
        <div className="messages-actions">
          <button
            className="btn btn-secondary"
            onClick={() => setShowSettingsModal(true)}
            title="Benachrichtigungseinstellungen"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M12 1v6m0 6v6m-6-6h6m6 0h6"></path>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
            Einstellungen
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
          >
            Alle als gelesen markieren
          </button>
        </div>
      </div>

      <div className="messages-container">
        {/* Left sidebar - Message list */}
        <div className="messages-list">
          <div className="messages-list-header">
            <div className="messages-filter">
              <button 
                className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                onClick={() => setFilter('all')}
              >
                Alle ({messages.length})
              </button>
              <button 
                className={`filter-btn ${filter === 'unread' ? 'active' : ''}`}
                onClick={() => setFilter('unread')}
              >
                Ungelesen ({unreadCount})
              </button>
              <button 
                className={`filter-btn ${filter === 'read' ? 'active' : ''}`}
                onClick={() => setFilter('read')}
              >
                Gelesen ({messages.length - unreadCount})
              </button>
            </div>
          </div>

          <div className="messages-list-content">
            {loading ? (
              <div className="loading">Laden...</div>
            ) : error ? (
              <div className="error">{error}</div>
            ) : messages.length === 0 ? (
              <div className="no-messages">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                  <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
                <p>Keine Nachrichten vorhanden</p>
              </div>
            ) : (
              messages.map(message => (
                <div
                  key={message.id}
                  className={`message-item ${!message.is_read ? 'unread' : ''} ${selectedMessage?.id === message.id ? 'selected' : ''}`}
                  onClick={() => handleSelectMessage(message)}
                >
                  <div className="message-item-header">
                    <div className="message-item-type">
                      {getMessageTypeIcon(message.message_type)}
                    </div>
                    <div className="message-item-subject">
                      {message.subject}
                    </div>
                    {!message.is_read && <div className="unread-indicator"></div>}
                  </div>
                  <div className="message-item-preview">
                    {message.content.substring(0, 100)}...
                  </div>
                  <div className="message-item-date">
                    {formatDate(message.created_at)}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right panel - Message detail */}
        <div className="message-detail">
          {selectedMessage ? (
            <>
              <div className="message-detail-header">
                <div className="message-detail-title">
                  <div className={`message-type-badge ${selectedMessage.message_type}`}>
                    {getMessageTypeIcon(selectedMessage.message_type)}
                    <span>{selectedMessage.message_type === 'info' ? 'Info' : selectedMessage.message_type === 'success' ? 'Erfolg' : selectedMessage.message_type === 'warning' ? 'Warnung' : 'Fehler'}</span>
                  </div>
                  <h2>{selectedMessage.subject}</h2>
                </div>
                <div className="message-detail-actions">
                  <button
                    className="btn-icon"
                    onClick={() => handleToggleRead(selectedMessage.id, selectedMessage.is_read)}
                    title={selectedMessage.is_read ? 'Als ungelesen markieren' : 'Als gelesen markieren'}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                      <polyline points="22,6 12,13 2,6"></polyline>
                    </svg>
                  </button>
                  <button
                    className="btn-icon btn-delete"
                    onClick={() => handleDeleteMessage(selectedMessage.id)}
                    title="Löschen"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                  </button>
                </div>
              </div>
              <div className="message-detail-meta">
                <span className="message-detail-date">{formatDate(selectedMessage.created_at)}</span>
              </div>
              <div className="message-detail-content">
                {renderMessageContent(selectedMessage.content)}
              </div>
            </>
          ) : (
            <div className="no-message-selected">
              <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                <polyline points="22,6 12,13 2,6"></polyline>
              </svg>
              <p>Wählen Sie eine Nachricht aus, um sie anzuzeigen</p>
            </div>
          )}
        </div>
      </div>

      {/* Notification Settings Modal */}
      <NotificationSettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        onSave={() => {
          // Reload messages after settings change
          loadMessages();
        }}
      />
    </div>
  );
};

export default Messages;

