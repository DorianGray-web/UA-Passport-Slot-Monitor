import { normalizeFreeText } from './validation.js';

const canonicalOrder = (values, order = []) => {
  const ranks = new Map(order.map((id, index) => [id, index]));
  return [...new Set(values || [])].sort((left, right) => {
    const leftRank = ranks.get(left) ?? Number.MAX_SAFE_INTEGER;
    const rightRank = ranks.get(right) ?? Number.MAX_SAFE_INTEGER;
    return leftRank - rightRank || left.localeCompare(right);
  });
};

export function applyExclusiveSelection(selected, id, checked, sentinel) {
  const current = selected || [];
  if (!checked) return current.filter((value) => value !== id);
  if (id === sentinel) return [id];
  return [...current.filter((value) => value !== sentinel && value !== id), id];
}

export function buildCanonicalAnswers(values, taxonomyOrder = {}) {
  const centreIds = canonicalOrder(values.centre_ids, taxonomyOrder.centres);
  const problemIds = canonicalOrder(values.problem_category_ids, taxonomyOrder.problems);
  const channelIds = canonicalOrder(values.notification_channel_ids, taxonomyOrder.channels);

  return {
    residence_region_id: values.residence_region_id,
    centre_ids: centreIds,
    other_centre_text: centreIds.includes('other_centre') ? normalizeFreeText(values.other_centre_text) : null,
    service_id: values.service_id,
    other_service_text: values.service_id === 'other' ? normalizeFreeText(values.other_service_text) : null,
    slot_search_experience: values.slot_search_experience,
    check_frequency: values.check_frequency,
    search_duration: values.slot_search_experience === 'not_started' ? null : values.search_duration ?? null,
    appointment_urgency: values.appointment_urgency ?? null,
    problem_category_ids: problemIds,
    other_problem_text: problemIds.includes('other') ? normalizeFreeText(values.other_problem_text) : null,
    cross_border_flexibility: values.cross_border_flexibility ?? null,
    notification_channel_ids: channelIds,
    other_notification_channel_text: channelIds.includes('other') ? normalizeFreeText(values.other_notification_channel_text) : null,
    primary_notification_channel_id: values.primary_notification_channel_id,
    manual_captcha_attitude: values.manual_captcha_attitude,
    early_testing_interest: values.early_testing_interest,
    additional_context: normalizeFreeText(values.additional_context, { multiline: true }),
  };
}

export function buildSurveyResponse({
  values,
  taxonomyOrder,
  responseId,
  locale,
  submittedAt,
  timezoneOffsetMinutes,
}) {
  return {
    response_id: responseId,
    survey_version: '1.0.0',
    contract_version: '2.0.0',
    source: 'survey_web_form',
    locale,
    submitted_at: submittedAt,
    answers: buildCanonicalAnswers(values, taxonomyOrder),
    consent: { research: Boolean(values.consent_research) },
    client: { timezone_offset_minutes: timezoneOffsetMinutes },
  };
}
