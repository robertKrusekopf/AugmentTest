import { useState } from 'react';
import PropTypes from 'prop-types';
import './ClubEmblem.css';

/**
 * ClubEmblem Component
 * 
 * A reusable component for displaying club emblems with proper error handling
 * and fallback to initials when the emblem fails to load.
 * 
 * Features:
 * - Prevents flickering by using React state instead of DOM manipulation
 * - Shows initials as fallback when emblem is not available or fails to load
 * - Supports different sizes via className
 * - Proper caching through browser cache headers
 * 
 * @param {string} emblemUrl - The URL of the club emblem (e.g., "/api/club-emblem/...")
 * @param {string} clubName - The name of the club (used for alt text and fallback initials)
 * @param {string} className - CSS class for styling (e.g., "club-emblem", "club-emblem-small")
 * @param {string} fallbackText - Optional custom fallback text (defaults to club initials)
 */
const ClubEmblem = ({ emblemUrl, clubName, className = 'club-emblem', fallbackText = null }) => {
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);

  // Generate fallback initials from club name
  const getInitials = () => {
    if (fallbackText) return fallbackText;
    if (!clubName) return '?';
    
    // Split by spaces and take first letter of each word
    const words = clubName.split(' ');
    if (words.length === 1) {
      // Single word: take first 2-3 characters
      return clubName.substring(0, Math.min(3, clubName.length)).toUpperCase();
    }
    // Multiple words: take first letter of each word (max 3)
    return words
      .slice(0, 3)
      .map(word => word[0])
      .join('')
      .toUpperCase();
  };

  const handleImageError = () => {
    setImageError(true);
    setImageLoading(false);
  };

  const handleImageLoad = () => {
    setImageLoading(false);
    setImageError(false);
  };

  // If no emblem URL or image failed to load, show fallback
  if (!emblemUrl || imageError) {
    return (
      <span className={`${className} emblem-fallback`}>
        {getInitials()}
      </span>
    );
  }

  return (
    <>
      <img
        src={emblemUrl}
        alt={`${clubName} Wappen`}
        className={`${className} ${imageLoading ? 'emblem-loading' : ''}`}
        onError={handleImageError}
        onLoad={handleImageLoad}
        loading="lazy"
      />
      {imageLoading && (
        <span className={`${className} emblem-fallback emblem-placeholder`}>
          {getInitials()}
        </span>
      )}
    </>
  );
};

ClubEmblem.propTypes = {
  emblemUrl: PropTypes.string,
  clubName: PropTypes.string.isRequired,
  className: PropTypes.string,
  fallbackText: PropTypes.string,
};

export default ClubEmblem;

