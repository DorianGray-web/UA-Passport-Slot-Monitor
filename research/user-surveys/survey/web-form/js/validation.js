const singleLinePattern = /^(?!.*(?:https?:\/\/|www\.|[^\s@]+@[^\s@]+\.[^\s@]+|@[_A-Za-z0-9]{2,}|\+?[0-9][0-9 ()-]{6,}[0-9]))[^<>\u0000-\u001F\u007F]*$/;

export function normalizeFreeText(value) {
  if (typeof value !== 'string') return null;
  const normalized = value.trim();
  return normalized || null;
}

function isTextValid(value, maxLength, multiline = false, minimumLength = 2) {
  if (typeof value !== 'string') return false;
  if (value.length < minimumLength || value.length > maxLength) return false;
  if (!multiline && /[\r\n]/.test(value)) return false;
  return (multiline ? !/[<>\u0000-\u0009\u000B-\u001F\u007F]/.test(value) : singleLinePattern.test(value));
}

export function validateAnswers(answers, taxonomies, partial = false) {
  const errors = {};
  if (!partial && answers.consent_research !== true) errors.consent_research = 'required';
  const required = ['residence_region_id', 'service_id', 'slot_search_experience', 'check_frequency', 'manual_captcha_attitude', 'early_testing_interest', 'primary_notification_channel_id'];
  if (!partial) for (const field of required) if (!answers[field]) errors[field] = 'required';
  if (!partial && !answers.centre_ids?.length) errors.centre_ids = 'required';
  if (answers.centre_ids?.length > 5 || (answers.centre_ids?.includes('not_decided') && answers.centre_ids.length > 1)) errors.centre_ids = 'invalid';
  if (answers.centre_ids?.includes('other_centre') && !isTextValid(answers.other_centre_text, 80)) errors.other_centre_text = 'invalid';
  if (answers.service_id === 'other' && !isTextValid(answers.other_service_text, 80)) errors.other_service_text = 'invalid';
  if (answers.problem_category_ids?.length > 5 || (answers.problem_category_ids?.includes('none') && answers.problem_category_ids.length > 1)) errors.problem_category_ids = 'invalid';
  if (answers.problem_category_ids?.includes('other') && !isTextValid(answers.other_problem_text, 160)) errors.other_problem_text = 'invalid';
  if (!partial && !answers.notification_channel_ids?.length) errors.notification_channel_ids = 'required';
  if (answers.notification_channel_ids?.length > 3 || (answers.notification_channel_ids?.includes('none') && answers.notification_channel_ids.length > 1)) errors.notification_channel_ids = 'invalid';
  if (answers.notification_channel_ids?.includes('other') && !isTextValid(answers.other_notification_channel_text, 80)) errors.other_notification_channel_text = 'invalid';
  if (answers.primary_notification_channel_id && !answers.notification_channel_ids?.includes(answers.primary_notification_channel_id)) errors.primary_notification_channel_id = 'invalid';
  if (answers.additional_context && !isTextValid(answers.additional_context, 500, true, 1)) errors.additional_context = 'invalid';
  const valid = {
    residence_region_id: ['eu', 'united_kingdom', 'canada', 'other_country'], service_id: ['international_passport', 'id_card', 'passport_exchange', 'id_and_passport', 'other'],
    slot_search_experience: ['not_started', 'searching_now', 'searched_before', 'booked_before'], check_frequency: ['several_times_daily', 'daily', 'several_times_weekly', 'occasionally', 'not_checking_yet'],
    manual_captcha_attitude: ['acceptable', 'acceptable_if_rare', 'require_full_automation', 'not_sure'], early_testing_interest: ['yes', 'no', 'maybe'],
    search_duration: ['under_1_week', 'one_to_4_weeks', 'one_to_3_months', 'over_3_months', 'not_sure'], appointment_urgency: ['within_2_weeks', 'within_1_month', 'within_3_months', 'later', 'not_sure'], cross_border_flexibility: ['yes', 'maybe', 'no', 'not_sure'],
  };
  for (const [field, values] of Object.entries(valid)) if (answers[field] && !values.includes(answers[field])) errors[field] = 'invalid';
  if (taxonomies && answers.centre_ids && !answers.centre_ids.every((id) => taxonomies.centres.has(id) || ['other_centre', 'not_decided'].includes(id))) errors.centre_ids = 'invalid';
  if (taxonomies && answers.problem_category_ids && !answers.problem_category_ids.every((id) => taxonomies.problems.has(id))) errors.problem_category_ids = 'invalid';
  if (taxonomies && answers.notification_channel_ids && !answers.notification_channel_ids.every((id) => taxonomies.channels.has(id))) errors.notification_channel_ids = 'invalid';
  return errors;
}
