import React, { useState } from 'react';

/**
 * FlagIcon Component - Zeigt Flaggen für verschiedene Nationalitäten an
 *
 * Unterstützt drei Modi:
 * 1. CSS-basierte Flaggen (Standard)
 * 2. Unicode-Emoji Flaggen (Fallback)
 * 3. Bild-basierte Flaggen (wenn Bilder verfügbar)
 */

const FlagIcon = ({ nationality, size = 'medium', mode = 'css' }) => {
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);

  // Mapping von Nationalitäten zu Ländercodes (Adjektive -> Ländercodes)
  const getCountryCode = (nationality) => {
    const countryMap = {
      'Deutsch': 'de',
      'Österreichisch': 'at',
      'Schweizerisch': 'ch',
      'Niederländisch': 'nl',
      'Belgisch': 'be',
      'Französisch': 'fr',
      'Italienisch': 'it',
      'Spanisch': 'es',
      'Polnisch': 'pl',
      'Tschechisch': 'cz',
      'Dänisch': 'dk',
      'Schwedisch': 'se',
      'Norwegisch': 'no',
      'Finnisch': 'fi',
      'Russisch': 'ru',
      'Amerikanisch': 'us',
      'Kanadisch': 'ca',
      'Australisch': 'au',
      'Japanisch': 'jp',
      'Südkoreanisch': 'kr',
      'Chinesisch': 'cn',
      'Brasilianisch': 'br',
      'Argentinisch': 'ar',
      'Mexikanisch': 'mx',
      'Türkisch': 'tr',
      'Griechisch': 'gr',
      'Portugiesisch': 'pt',
      'Kroatisch': 'hr',
      'Serbisch': 'rs',
      'Slowenisch': 'si',
      'Ungarisch': 'hu',
      'Rumänisch': 'ro',
      'Bulgarisch': 'bg',
      'Ukrainisch': 'ua',
      'Slowakisch': 'sk',
      'Litauisch': 'lt',
      'Lettisch': 'lv',
      'Estnisch': 'ee',
      // Fallback für Ländernamen (falls jemand die verwendet)
      'Deutschland': 'de',
      'Österreich': 'at',
      'Schweiz': 'ch',
      'Niederlande': 'nl',
      'Belgien': 'be',
      'Frankreich': 'fr',
      'Italien': 'it',
      'Spanien': 'es',
      'Polen': 'pl',
      'Tschechien': 'cz',
      'Dänemark': 'dk',
      'Schweden': 'se',
      'Norwegen': 'no',
      'Finnland': 'fi',
      'Russland': 'ru',
      'USA': 'us',
      'Kanada': 'ca',
      'Australien': 'au',
      'Japan': 'jp',
      'Südkorea': 'kr',
      'China': 'cn',
      'Brasilien': 'br',
      'Argentinien': 'ar',
      'Mexiko': 'mx',
      'Türkei': 'tr',
      'Griechenland': 'gr',
      'Portugal': 'pt',
      'Kroatien': 'hr',
      'Serbien': 'rs',
      'Slowenien': 'si',
      'Ungarn': 'hu',
      'Rumänien': 'ro',
      'Bulgarien': 'bg',
      'Ukraine': 'ua',
      'Slowakei': 'sk',
      'Litauen': 'lt',
      'Lettland': 'lv',
      'Estland': 'ee'
    };

    return countryMap[nationality] || 'unknown';
  };

  // Unicode-Emoji Flaggen (Fallback)
  const getUnicodeFlag = (nationality) => {
    const flagMap = {
      'Deutsch': '🇩🇪',
      'Österreichisch': '🇦🇹',
      'Schweizerisch': '🇨🇭',
      'Niederländisch': '🇳🇱',
      'Belgisch': '🇧🇪',
      'Französisch': '🇫🇷',
      'Italienisch': '🇮🇹',
      'Spanisch': '🇪🇸',
      'Polnisch': '🇵🇱',
      'Tschechisch': '🇨🇿',
      'Dänisch': '🇩🇰',
      'Schwedisch': '🇸🇪',
      'Norwegisch': '🇳🇴',
      'Finnisch': '🇫🇮',
      'Russisch': '🇷🇺',
      'Amerikanisch': '🇺🇸',
      'Kanadisch': '🇨🇦',
      'Australisch': '🇦🇺',
      'Japanisch': '🇯🇵',
      'Südkoreanisch': '🇰🇷',
      'Chinesisch': '🇨🇳',
      'Brasilianisch': '🇧🇷',
      'Argentinisch': '🇦🇷',
      'Mexikanisch': '🇲🇽',
      'Türkisch': '🇹🇷',
      'Griechisch': '🇬🇷',
      'Portugiesisch': '🇵🇹',
      'Kroatisch': '🇭🇷',
      'Serbisch': '🇷🇸',
      'Slowenisch': '🇸🇮',
      'Ungarisch': '🇭🇺',
      'Rumänisch': '🇷🇴',
      'Bulgarisch': '🇧🇬',
      'Ukrainisch': '🇺🇦',
      'Slowakisch': '🇸🇰',
      'Litauisch': '🇱🇹',
      'Lettisch': '🇱🇻',
      'Estnisch': '🇪🇪',
      // Fallback für Ländernamen
      'Deutschland': '🇩🇪',
      'Österreich': '🇦🇹',
      'Schweiz': '🇨🇭',
      'Niederlande': '🇳🇱',
      'Belgien': '🇧🇪',
      'Frankreich': '🇫🇷',
      'Italien': '🇮🇹',
      'Spanien': '🇪🇸',
      'Polen': '🇵🇱',
      'Tschechien': '🇨🇿',
      'Dänemark': '🇩🇰',
      'Schweden': '🇸🇪',
      'Norwegen': '🇳🇴',
      'Finnland': '🇫🇮',
      'Russland': '🇷🇺',
      'USA': '🇺🇸',
      'Kanada': '🇨🇦',
      'Australien': '🇦🇺',
      'Japan': '🇯🇵',
      'Südkorea': '🇰🇷',
      'China': '🇨🇳',
      'Brasilien': '🇧🇷',
      'Argentinien': '🇦🇷',
      'Mexiko': '🇲🇽',
      'Türkei': '🇹🇷',
      'Griechenland': '🇬🇷',
      'Portugal': '🇵🇹',
      'Kroatien': '🇭🇷',
      'Serbien': '🇷🇸',
      'Slowenien': '🇸🇮',
      'Ungarn': '🇭🇺',
      'Rumänien': '🇷🇴',
      'Bulgarien': '🇧🇬',
      'Ukraine': '🇺🇦',
      'Slowakei': '🇸🇰',
      'Litauen': '🇱🇹',
      'Lettland': '🇱🇻',
      'Estland': '🇪🇪'
    };

    return flagMap[nationality] || '🏳️';
  };

  const countryCode = getCountryCode(nationality);

  // Größen-Klassen
  const sizeClass = {
    small: 'flag-small',
    medium: 'flag-medium',
    large: 'flag-large'
  }[size] || 'flag-medium';

  // CSS-basierte Flaggen (Standard)
  if (mode === 'css') {
    return (
      <span 
        className={`flag ${sizeClass} flag-${countryCode}`}
        title={nationality}
        aria-label={`Flagge von ${nationality}`}
      ></span>
    );
  }

  // Unicode-Emoji Flaggen (Fallback)
  if (mode === 'emoji') {
    return (
      <span 
        className={`flag-emoji ${sizeClass}`}
        title={nationality}
        aria-label={`Flagge von ${nationality}`}
      >
        {getUnicodeFlag(nationality)}
      </span>
    );
  }

  // Bild-basierte Flaggen
  if (mode === 'image') {
    const handleImageError = () => {
      setImageError(true);
      setImageLoading(false);
    };

    const handleImageLoad = () => {
      setImageLoading(false);
      setImageError(false);
    };

    // Wenn Bild fehlgeschlagen ist, verwende CSS-Flagge als Fallback
    if (imageError) {
      return (
        <span
          className={`flag ${sizeClass} flag-${countryCode}`}
          title={nationality}
          aria-label={`Flagge von ${nationality}`}
        ></span>
      );
    }

    // Versuche SVG zu laden
    const flagPath = `/src/assets/flags/${countryCode}.svg`;

    return (
      <>
        <img
          src={flagPath}
          alt={nationality}
          className={`flag-image ${sizeClass} ${imageLoading ? 'flag-loading' : ''}`}
          title={nationality}
          onError={handleImageError}
          onLoad={handleImageLoad}
          loading="lazy"
        />
        {imageLoading && (
          <span
            className={`flag ${sizeClass} flag-${countryCode} flag-placeholder`}
            title={nationality}
            aria-label={`Flagge von ${nationality}`}
          ></span>
        )}
      </>
    );
  }

  // Standard: CSS-basierte Flagge
  return (
    <span 
      className={`flag ${sizeClass} flag-${countryCode}`}
      title={nationality}
      aria-label={`Flagge von ${nationality}`}
    ></span>
  );
};

export default FlagIcon;
