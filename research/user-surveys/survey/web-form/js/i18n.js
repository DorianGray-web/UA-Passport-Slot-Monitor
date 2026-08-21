import { translations } from '../config/translations.js';

export function getMessages(locale) {
  return translations[locale] || translations.en;
}

export function text(messages, path, fallback = '') {
  const value = path.split('.').reduce((current, key) => current?.[key], messages);
  return typeof value === 'string' ? value : fallback;
}
