import { loadTaxonomies } from '../config/centres.js';
import { questions, sections } from '../config/questions.js';
import { getMessages, text } from './i18n.js';
import { submitSurvey } from './api.js';
import { normalizeFreeText, validateAnswers } from './validation.js';

const form = document.querySelector('#survey-form');
const status = document.querySelector('#form-status');
const localePicker = document.querySelector('#locale-picker');
const debugMode = new URLSearchParams(window.location.search).get('debug') === '1';
const debugPanel = document.querySelector('#debug-panel');
const debugResponseId = document.querySelector('#debug-response-id');
const debugPayload = document.querySelector('#debug-payload');
const state = { locale: document.documentElement.lang || 'en', section: 0, values: { consent_research: false }, errors: {}, submitting: false, responseId: crypto.randomUUID() };
let taxonomies;

const fieldFor = (question) => question.field || question.id;
const active = (question) => !question.showWhen || state.values[question.showWhen[0]]?.includes?.(question.showWhen[1]) || state.values[question.showWhen[0]] === question.showWhen[1];
const optionLabel = (messages, question, id) => text(messages, `questions.${question.id}.options.${id}`, id);

function createChoice(question, id, label, multiple = false) {
  const wrapper = document.createElement('label'); wrapper.className = 'choice';
  const input = document.createElement('input'); input.type = multiple ? 'checkbox' : 'radio'; input.name = fieldFor(question); input.value = id; input.checked = multiple ? state.values[fieldFor(question)]?.includes(id) : state.values[fieldFor(question)] === id;
  input.addEventListener('change', () => { if (multiple && input.checked) { const systemIds = question.type === 'centres' ? ['other_centre', 'not_decided'] : ['other', 'none']; form.querySelectorAll(`input[name="${fieldFor(question)}"]`).forEach((node) => { if (node !== input && ((systemIds.includes(id) && !systemIds.includes(node.value)) || (!systemIds.includes(id) && systemIds.includes(node.value) && node.checked))) node.checked = false; }); } state.values[fieldFor(question)] = multiple ? [...form.querySelectorAll(`input[name="${fieldFor(question)}"]:checked`)].map((node) => node.value) : input.value; render(); });
  wrapper.append(input, document.createTextNode(label)); return wrapper;
}

function taxonomyOptions(question) {
  if (question.type === 'problems') return [...taxonomies.problemsData].sort((a, b) => a.sort_order - b.sort_order).map((item) => [item.id, item.labels[state.locale] || item.labels.en]);
  if (question.type === 'channels') return [...taxonomies.channelsData].sort((a, b) => a.sort_order - b.sort_order).map((item) => [item.id, item.labels[state.locale] || item.labels.en]);
  return [];
}

function groupedCentreOptions() {
  const collator = new Intl.Collator(state.locale, { sensitivity: 'base' });
  const countriesByCode = new Map(taxonomies.countriesData.map((country) => [country.country_code, country]));
  const groups = new Map();
  for (const centre of taxonomies.centresData) {
    const country = countriesByCode.get(centre.country_code);
    if (!country) continue;
    if (!groups.has(centre.country_code)) groups.set(centre.country_code, { country, centres: [] });
    groups.get(centre.country_code).centres.push(centre);
  }
  return [...groups.values()]
    .sort((a, b) => collator.compare(a.country.labels[state.locale] || a.country.labels.en, b.country.labels[state.locale] || b.country.labels.en))
    .map((group) => ({
      label: group.country.labels[state.locale] || group.country.labels.en,
      centres: group.centres.sort((a, b) => collator.compare(a.labels[state.locale] || a.labels.en, b.labels[state.locale] || b.labels.en)),
    }));
}

function renderQuestion(question, messages) {
  if (!active(question)) return null;
  const field = fieldFor(question); const wrapper = document.createElement('fieldset'); wrapper.className = 'question'; wrapper.dataset.field = field;
  const legend = document.createElement('legend'); legend.textContent = text(messages, `questions.${question.id}.title`, question.id); wrapper.append(legend);
  const help = text(messages, `questions.${question.id}.help`); if (help) { const p = document.createElement('p'); p.className = 'help'; p.textContent = help; wrapper.append(p); }
  if (question.type === 'checkbox') { const label = document.createElement('label'); label.className = 'choice'; const input = document.createElement('input'); input.type = 'checkbox'; input.name = field; input.checked = Boolean(state.values.consent_research); input.addEventListener('change', (event) => { state.values.consent_research = event.target.checked; }); label.append(input, document.createTextNode(text(messages, 'questions.research_consent.title'))); wrapper.append(label); }
  else if (question.type === 'text' || question.type === 'textarea') { const input = document.createElement(question.type === 'textarea' ? 'textarea' : 'input'); input.name = field; input.value = state.values[field] || ''; input.maxLength = question.maxLength; input.rows = 4; input.addEventListener('input', () => { state.values[field] = input.value; }); wrapper.append(input); }
  else if (question.type === 'centres') {
    for (const group of groupedCentreOptions()) {
      const heading = document.createElement('h3'); heading.className = 'country-heading'; heading.textContent = group.label; wrapper.append(heading);
      for (const centre of group.centres) wrapper.append(createChoice(question, centre.centre_id, centre.labels[state.locale] || centre.labels.en, true));
    }
    const surveyOptions = document.createElement('div'); surveyOptions.className = 'survey-options';
    for (const item of taxonomies.centreSystems) surveyOptions.append(createChoice(question, item.centre_id, item.labels[state.locale] || item.labels.en, true));
    wrapper.append(surveyOptions);
  }
  else { let options = question.options?.map((id) => [id, optionLabel(messages, question, id)]) || taxonomyOptions(question); if (question.type === 'primary-channel') options = taxonomyOptions({ type: 'channels', id: 'notification_channels' }).filter(([id]) => state.values.notification_channel_ids?.includes(id)); options.forEach(([id, label]) => wrapper.append(createChoice(question, id, label, ['problems', 'channels'].includes(question.type)))); }
  if (state.errors[field]) { wrapper.classList.add('has-error'); const error = document.createElement('p'); error.className = 'error'; error.id = `${field}-error`; error.textContent = text(messages, `questions.${question.id}.error.${state.errors[field]}`, text(messages, 'controls.invalid')); wrapper.append(error); wrapper.querySelectorAll('input, textarea').forEach((node) => { node.setAttribute('aria-describedby', error.id); node.setAttribute('aria-invalid', 'true'); }); }
  return wrapper;
}

function render() {
  const messages = getMessages(state.locale); document.documentElement.lang = state.locale; document.title = messages.title; localePicker.setAttribute('aria-label', messages.language); document.querySelectorAll('[data-i18n]').forEach((node) => { const value = text(messages, node.dataset.i18n); if (value) node.textContent = value; }); form.replaceChildren();
  const sectionId = sections[state.section]; const heading = document.createElement('h2'); heading.textContent = text(messages, `sections.${sectionId}`); form.append(heading);
  questions.filter((question) => question.section === sectionId).forEach((question) => { const node = renderQuestion(question, messages); if (node) form.append(node); });
  const nav = document.createElement('div'); nav.className = 'form-actions';
  if (state.section > 0) { const back = document.createElement('button'); back.type = 'button'; back.className = 'secondary'; back.textContent = text(messages, 'controls.back'); back.addEventListener('click', () => { state.section -= 1; render(); }); nav.append(back); }
  const next = document.createElement('button'); next.type = state.section === sections.length - 1 ? 'submit' : 'button'; next.textContent = state.submitting ? text(messages, 'controls.submitting') : state.section === sections.length - 1 ? text(messages, 'controls.submit') : text(messages, 'controls.next'); next.disabled = state.submitting; if (next.type === 'button') next.addEventListener('click', advance); nav.append(next); form.append(nav);
  status.textContent = state.status || '';
}

function showDebugPayload(payload) {
  if (!debugMode) return;
  debugPanel.hidden = false;
  debugResponseId.textContent = payload.response_id;
  debugPayload.textContent = JSON.stringify(payload, null, 2);
}

function visibleAnswers() { const values = { ...state.values }; if (values.slot_search_experience === 'not_started') values.search_duration = null; for (const field of ['other_centre_text', 'other_service_text', 'other_problem_text', 'other_notification_channel_text']) if (!active(questions.find((question) => fieldFor(question) === field))) values[field] = null; for (const field of ['other_centre_text', 'other_service_text', 'other_problem_text', 'other_notification_channel_text', 'additional_context']) values[field] = normalizeFreeText(values[field]); if (!values.problem_category_ids) values.problem_category_ids = []; if (!values.notification_channel_ids) values.notification_channel_ids = []; return values; }
function validateCurrent() {
  const answers = visibleAnswers();
  const errors = validateAnswers(answers, taxonomies, true);
  for (const question of questions.filter((item) => item.section === sections[state.section] && item.required && active(item))) {
    const field = fieldFor(question); const value = field === 'consent_research' ? answers.consent_research : answers[field];
    if ((question.type === 'checkbox' && value !== true) || (question.type !== 'checkbox' && (!value || (Array.isArray(value) && !value.length)))) errors[field] = 'required';
  }
  state.errors = errors; return Object.keys(errors).length === 0;
}
function advance() { if (!validateCurrent()) { state.status = text(getMessages(state.locale), 'controls.invalid'); render(); return; } state.section += 1; state.errors = {}; state.status = ''; render(); }

form.addEventListener('submit', async (event) => { event.preventDefault(); if (state.submitting || !validateCurrent()) { state.status = text(getMessages(state.locale), 'controls.invalid'); render(); return; } state.submitting = true; state.status = text(getMessages(state.locale), 'controls.submitting'); render(); try { const answers = visibleAnswers(); const payload = { response_id: state.responseId, survey_version: '1.0.0', contract_version: '2.0.0', source: 'survey_web_form', locale: state.locale, submitted_at: new Date().toISOString(), answers: { ...answers, other_centre_text: normalizeFreeText(answers.other_centre_text), other_service_text: normalizeFreeText(answers.other_service_text), other_problem_text: normalizeFreeText(answers.other_problem_text), other_notification_channel_text: normalizeFreeText(answers.other_notification_channel_text), additional_context: normalizeFreeText(answers.additional_context) }, consent: { research: Boolean(answers.consent_research) }, client: { timezone_offset_minutes: new Date().getTimezoneOffset() * -1 } }; const result = await submitSurvey(payload); state.submitting = false; state.status = result.status === 'demo' ? text(getMessages(state.locale), 'controls.demoSuccess') : text(getMessages(state.locale), 'controls.success'); showDebugPayload(payload); render(); } catch { state.submitting = false; state.status = text(getMessages(state.locale), 'controls.error'); render(); } });
localePicker.addEventListener('change', () => { state.locale = localePicker.value; render(); });

loadTaxonomies().then((data) => { taxonomies = { centresData: data.centres.centres, centreSystems: data.centres.system_options, countriesData: data.centres.countries, problemsData: data.problems.problem_categories, channelsData: data.channels.notification_channels, centres: new Set(data.centres.centres.map((item) => item.centre_id)), problems: new Set(data.problems.problem_categories.map((item) => item.id)), channels: new Set(data.channels.notification_channels.map((item) => item.id)) }; render(); }).catch(() => { status.textContent = text(getMessages(state.locale), 'controls.taxonomyError'); });
