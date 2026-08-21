import { normalizeFreeText, validateAnswers } from '../js/validation.js';

const taxonomies = {
  centres: new Set(['berlin', 'munich']),
  problems: new Set(['none', 'other']),
  channels: new Set(['none', 'telegram', 'other']),
};

const validAnswers = {
  consent_research: true,
  residence_region_id: 'eu',
  centre_ids: ['munich'],
  other_centre_text: null,
  service_id: 'id_card',
  other_service_text: null,
  slot_search_experience: 'not_started',
  check_frequency: 'not_checking_yet',
  search_duration: null,
  appointment_urgency: null,
  problem_category_ids: ['none'],
  other_problem_text: null,
  cross_border_flexibility: null,
  notification_channel_ids: ['none'],
  other_notification_channel_text: null,
  primary_notification_channel_id: 'none',
  manual_captcha_attitude: 'not_sure',
  early_testing_interest: 'maybe',
  additional_context: null,
};

export function testValidObject() {
  if (Object.keys(validateAnswers(validAnswers, taxonomies)).length !== 0) throw new Error('Expected valid contract answers');
}

export function testConsentRequired() {
  const errors = validateAnswers({ ...validAnswers, consent_research: false }, taxonomies);
  if (errors.consent_research !== 'required') throw new Error('Expected required consent error');
}

export function testCentreExclusivity() {
  const errors = validateAnswers({ ...validAnswers, centre_ids: ['munich', 'not_decided'] }, taxonomies);
  if (errors.centre_ids !== 'invalid') throw new Error('Expected not_decided exclusivity error');
}

export function testFreeTextNormalization() {
  if (normalizeFreeText('  Viber  ') !== 'Viber') throw new Error('Expected surrounding whitespace to be trimmed');
  if (normalizeFreeText('Some  text') !== 'Some  text') throw new Error('Expected internal whitespace to be preserved');
  if (normalizeFreeText('   ') !== null) throw new Error('Expected whitespace-only text to become null');
  if (normalizeFreeText(null) !== null) throw new Error('Expected inactive text to remain null');
}

export function testOptionalWhitespaceIsEmpty() {
  if (normalizeFreeText('   ') !== null) throw new Error('Expected optional whitespace-only context to be empty');
}
