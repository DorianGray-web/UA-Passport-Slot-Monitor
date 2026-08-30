export const questions = Object.freeze([
  { id: 'research_consent', field: 'consent_research', section: 'introduction', type: 'checkbox', required: true },
  { id: 'residence_region', field: 'residence_region_id', section: 'situation', type: 'radio', required: true, options: ['eu', 'united_kingdom', 'canada', 'other_country'] },
  { id: 'document_service', field: 'service_id', section: 'situation', type: 'radio', required: true, options: ['international_passport', 'id_card', 'passport_exchange', 'id_and_passport', 'other'] },
  { id: 'other_service_text', section: 'situation', type: 'text', required: true, maxLength: 80, showWhen: ['service_id', 'other'] },
  { id: 'slot_search_experience', section: 'situation', type: 'radio', required: true, options: ['not_started', 'searching_now', 'searched_before', 'booked_before'] },
  { id: 'check_frequency', section: 'situation', type: 'radio', required: true, options: ['several_times_daily', 'daily', 'several_times_weekly', 'occasionally', 'not_checking_yet'] },
  { id: 'search_duration', section: 'situation', type: 'radio', required: false, options: ['under_1_week', 'one_to_4_weeks', 'one_to_3_months', 'over_3_months', 'not_sure'], showUnless: ['slot_search_experience', 'not_started'] },
  { id: 'appointment_urgency', section: 'situation', type: 'radio', required: false, options: ['within_2_weeks', 'within_1_month', 'within_3_months', 'later', 'not_sure'] },
  { id: 'desired_centres', field: 'centre_ids', section: 'centres', type: 'centres', required: true },
  { id: 'other_centre_text', section: 'centres', type: 'text', required: true, maxLength: 80, showWhen: ['centre_ids', 'other_centre'] },
  { id: 'problem_categories', field: 'problem_category_ids', section: 'problems', type: 'problems', required: false },
  { id: 'other_problem_text', section: 'problems', type: 'text', required: true, maxLength: 160, showWhen: ['problem_category_ids', 'other'] },
  { id: 'cross_border_flexibility', section: 'problems', type: 'radio', required: false, options: ['yes', 'maybe', 'no', 'not_sure'] },
  { id: 'notification_channels', field: 'notification_channel_ids', section: 'notifications', type: 'channels', required: true },
  { id: 'other_notification_channel_text', section: 'notifications', type: 'text', required: true, maxLength: 80, showWhen: ['notification_channel_ids', 'other'] },
  { id: 'primary_notification_channel', field: 'primary_notification_channel_id', section: 'notifications', type: 'primary-channel', required: true },
  { id: 'manual_captcha_attitude', section: 'notifications', type: 'radio', required: true, options: ['acceptable', 'acceptable_if_rare', 'require_full_automation', 'not_sure'] },
  { id: 'early_testing_interest', section: 'testing', type: 'radio', required: true, options: ['yes', 'no', 'maybe'] },
  { id: 'additional_context', section: 'testing', type: 'textarea', required: false, maxLength: 500 },
]);

export const sections = Object.freeze(['introduction', 'situation', 'centres', 'problems', 'notifications', 'testing']);
