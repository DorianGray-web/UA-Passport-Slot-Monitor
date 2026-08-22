import { applyExclusiveSelection, buildCanonicalAnswers, buildSurveyResponse } from '../js/payload.js';
import { normalizeFreeText, validateAnswers } from '../js/validation.js';

const taxonomies = {
  centres: new Set(['berlin', 'munich']),
  problems: new Set(['none', 'no_slots_found', 'other']),
  channels: new Set(['none', 'telegram', 'other']),
};

const taxonomyOrder = {
  centres: ['berlin', 'munich', 'other_centre', 'not_decided'],
  problems: ['no_slots_found', 'other', 'none'],
  channels: ['telegram', 'other', 'none'],
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

const assert = (condition, message) => { if (!condition) throw new Error(message); };

export function testValidObject() {
  assert(Object.keys(validateAnswers(validAnswers, taxonomies)).length === 0, 'Expected valid contract answers');
}

export function testConsentRequired() {
  const errors = validateAnswers({ ...validAnswers, consent_research: false }, taxonomies);
  assert(errors.consent_research === 'required', 'Expected required consent error');
}

export function testCentreExclusivity() {
  const errors = validateAnswers({ ...validAnswers, centre_ids: ['munich', 'not_decided'] }, taxonomies);
  assert(errors.centre_ids === 'invalid', 'Expected not_decided exclusivity error');
  assert(JSON.stringify(applyExclusiveSelection(['munich'], 'not_decided', true, 'not_decided')) === '["not_decided"]', 'Expected sentinel to clear concrete selections');
  assert(JSON.stringify(applyExclusiveSelection(['not_decided'], 'munich', true, 'not_decided')) === '["munich"]', 'Expected concrete selection to clear sentinel');
}

export function testFreeTextNormalization() {
  assert(normalizeFreeText('  Viber\u00a0 channel  ') === 'Viber channel', 'Expected horizontal whitespace to be normalized');
  assert(normalizeFreeText('Cafe\u0301') === 'Caf\u00e9', 'Expected NFC normalization');
  assert(normalizeFreeText(' first\r\n\r\n second ', { multiline: true }) === 'first\n second', 'Expected canonical multiline line endings');
  assert(normalizeFreeText('   ') === null, 'Expected whitespace-only text to become null');
  assert(normalizeFreeText(null) === null, 'Expected inactive text to remain null');
}

export function testAdditionalContextPiiValidation() {
  for (const value of ['first line\nname@example.com', 'first line\nhttps://example.com', 'first line\n@handle', 'first line\n+31 20 123 4567']) {
    const errors = validateAnswers({ ...validAnswers, additional_context: value }, taxonomies);
    assert(errors.additional_context === 'invalid', `Expected multiline PII rejection for ${value}`);
  }
  assert(!validateAnswers({ ...validAnswers, additional_context: 'First paragraph\nSecond paragraph' }, taxonomies).additional_context, 'Expected ordinary multiline context to be accepted');
}

export async function testCanonicalPayloadConstruction() {
  const schema = await fetch('/research/user-surveys/shared/schemas/survey-response.schema.json').then((response) => response.json());
  const values = {
    ...validAnswers,
    centre_ids: ['munich', 'berlin'],
    problem_category_ids: ['other', 'no_slots_found'],
    other_problem_text: '  Another\u00a0 problem  ',
    notification_channel_ids: ['other', 'telegram'],
    other_notification_channel_text: '  Signal  ',
    primary_notification_channel_id: 'telegram',
  };
  const payloads = ['uk', 'ru', 'en'].map((locale) => buildSurveyResponse({
    values,
    taxonomyOrder,
    responseId: '123e4567-e89b-42d3-a456-426614174000',
    locale,
    submittedAt: '2026-08-22T12:00:00.000Z',
    timezoneOffsetMinutes: 120,
  }));
  const expectedKeys = [...schema.$defs.answers.required].sort();
  for (const payload of payloads) {
    assert(JSON.stringify(Object.keys(payload.answers).sort()) === JSON.stringify(expectedKeys), 'Expected exact schema-required answers keys');
    assert(!Object.hasOwn(payload.answers, 'consent_research'), 'Expected consent only at envelope root');
    assert(payload.consent.research === true, 'Expected root research consent');
    assert(payload.answers.search_duration === null && payload.answers.appointment_urgency === null && payload.answers.cross_border_flexibility === null, 'Expected required nullable fields to materialize as null');
    assert(JSON.stringify(payload.answers.centre_ids) === '["berlin","munich"]', 'Expected canonical centre ordering');
    assert(JSON.stringify(payload.answers.problem_category_ids) === '["no_slots_found","other"]', 'Expected canonical problem ordering');
    assert(JSON.stringify(payload.answers.notification_channel_ids) === '["telegram","other"]', 'Expected canonical channel ordering');
    assert(payload.answers.other_problem_text === 'Another problem', 'Expected conditional free text normalization');
  }
  assert(JSON.stringify(payloads[0].answers) === JSON.stringify(payloads[1].answers) && JSON.stringify(payloads[1].answers) === JSON.stringify(payloads[2].answers), 'Expected locale-independent analytical answers');
}

export function testInactiveConditionalFieldsMaterializeAsNull() {
  const answers = buildCanonicalAnswers({ ...validAnswers, other_service_text: 'stale', search_duration: 'under_1_week' }, taxonomyOrder);
  assert(answers.other_service_text === null, 'Expected inactive other service text to be null');
  assert(answers.search_duration === null, 'Expected hidden search duration to be null');
}
