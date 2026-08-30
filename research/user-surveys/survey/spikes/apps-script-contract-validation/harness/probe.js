const SPIKE_VERSION = '3.0.0';
const FIXTURE_PATH = '../fixtures/valid-survey-response.json';
const endpointInput = document.querySelector('#endpoint');
const matrix = document.querySelector('#matrix');
const fixtureStatus = document.querySelector('#fixture-status');
const copyOutput = document.querySelector('#copy-output');
const results = [];

let fixtureTemplate = null;
let acceptedFixture = null;

const CASES = [
  { id: '1', name: 'Valid canonical response', expected: 'ACCEPTED', writeExpected: true },
  { id: '2', name: 'Exact in-memory repeat', expected: 'DUPLICATE_ACCEPTED', writeExpected: false, dependsOnAccepted: true },
  { id: '3', name: 'Malformed JSON', expected: 'INVALID_REQUEST', writeExpected: false },
  { id: '4', name: 'Missing required nullable property', expected: 'INVALID_REQUEST', writeExpected: false },
  { id: '5', name: 'Invalid response_id UUID', expected: 'INVALID_REQUEST', writeExpected: false },
  { id: '6', name: 'Invalid centre taxonomy ID', expected: 'INVALID_REQUEST', writeExpected: false },
  { id: '7', name: 'Wrong field type', expected: 'INVALID_REQUEST', writeExpected: false },
  { id: '8', name: 'Unsupported contract_version', expected: 'UNSUPPORTED_CONTRACT', writeExpected: false },
  { id: '9', name: 'Controlled transient failure', expected: 'TEMPORARY_FAILURE', writeExpected: false, transientControl: true },
  { id: '10', name: 'Same identity, different content', expected: 'OPEN_IDENTITY_CONTENT_CONFLICT', writeExpected: false, dependsOnAccepted: true, openCase: true },
];

function clone(value) { return JSON.parse(JSON.stringify(value)); }

function endpointUrl() {
  const url = new URL(endpointInput.value);
  if (url.protocol !== 'https:' || url.hostname !== 'script.google.com' || !url.pathname.endsWith('/exec')) {
    throw new Error('Enter a temporary HTTPS script.google.com endpoint ending in /exec.');
  }
  url.search = '';
  url.hash = '';
  return url;
}

function freshFixture() {
  const fixture = clone(fixtureTemplate);
  fixture.response_id = crypto.randomUUID();
  fixture.submitted_at = new Date().toISOString();
  return fixture;
}

function requestFor(testCase) {
  if (testCase.id === '2') return { rawBody: JSON.stringify(acceptedFixture), responseId: acceptedFixture.response_id };
  if (testCase.id === '10') {
    const changed = clone(acceptedFixture);
    changed.answers.early_testing_interest = changed.answers.early_testing_interest === 'yes' ? 'maybe' : 'yes';
    return { rawBody: JSON.stringify(changed), responseId: changed.response_id };
  }

  const payload = freshFixture();
  if (testCase.id === '3') return { rawBody: '{"malformed":', responseId: null };
  if (testCase.id === '4') delete payload.answers.appointment_urgency;
  if (testCase.id === '5') payload.response_id = 'not-a-uuid';
  if (testCase.id === '6') payload.answers.centre_ids = ['nonexistent_centre'];
  if (testCase.id === '7') payload.answers.problem_category_ids = 'none';
  if (testCase.id === '8') payload.contract_version = '999.0.0';
  return { rawBody: JSON.stringify(payload), responseId: payload.response_id };
}

function safeError(error) {
  return {
    name: error instanceof Error ? error.name : 'Error',
    message: error instanceof Error ? error.message : 'Request failed',
  };
}

function classify(testCase, responseBody) {
  if (testCase.openCase) {
    return responseBody && !responseBody.outcome && responseBody.spike_result === 'OPEN_IDENTITY_CONTENT_CONFLICT'
      ? 'OPEN'
      : 'FAIL';
  }
  return responseBody && responseBody.outcome === testCase.expected ? 'PASS' : 'FAIL';
}

function sanitizedResponse(response) {
  if (!response || typeof response !== 'object') return response;
  return {
    spike_version: response.spike_version || null,
    outcome: response.outcome || null,
    spike_result: response.spike_result || null,
    result_scope: response.result_scope || null,
    diagnostic: response.diagnostic || null,
  };
}

async function executeCase(testCase) {
  const card = document.querySelector(`[data-case-card="${testCase.id}"]`);
  const status = card.querySelector('.status');
  const output = card.querySelector('pre');
  status.textContent = 'RUNNING';
  status.dataset.state = 'RUNNING';
  output.textContent = 'Request in progress…';
  const started = performance.now();

  let request;
  const summary = {
    spike_version: SPIKE_VERSION,
    case_id: testCase.id,
    case_name: testCase.name,
    expected: testCase.openCase ? 'OPEN SPIKE-ONLY conflict observation' : testCase.expected,
    physical_write_expected: testCase.writeExpected,
  };

  try {
    if (!fixtureTemplate) throw new Error('Synthetic fixture is not ready.');
    if (testCase.dependsOnAccepted && !acceptedFixture) throw new Error('Run Case 1 successfully first.');
    request = requestFor(testCase);
    summary.request_response_id = request.responseId;
    const url = endpointUrl();
    if (testCase.transientControl) url.searchParams.set('spike_control', 'temporary_failure');

    const response = await fetch(url, {
      method: 'POST',
      mode: 'cors',
      headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
      body: request.rawBody,
    });
    const bodyText = await response.text();
    let body = null;
    try { body = JSON.parse(bodyText); } catch (error) { summary.response_parse = 'non_json_response'; }

    summary.http_status = response.status;
    summary.response_type = response.type;
    summary.redirected = response.redirected;
    summary.final_host = response.url ? new URL(response.url).hostname : null;
    summary.final_path = response.redirected ? 'REDACTED_PLATFORM_REDIRECT_PATH' : 'DIRECT_PATH_REDACTED';
    summary.duration_ms = Math.round(performance.now() - started);
    summary.observed_outcome = body && body.outcome ? body.outcome : null;
    summary.spike_result = body && body.spike_result ? body.spike_result : null;
    summary.response = sanitizedResponse(body);
    summary.classification = classify(testCase, body);

    if (testCase.id === '1' && summary.classification === 'PASS') {
      acceptedFixture = JSON.parse(request.rawBody);
      updateDependentButtons();
    }
  } catch (error) {
    summary.duration_ms = Math.round(performance.now() - started);
    summary.classification = 'NETWORK_ERROR';
    summary.error = safeError(error);
  }

  results.push(summary);
  status.textContent = summary.classification;
  status.dataset.state = summary.classification;
  output.textContent = JSON.stringify(summary, null, 2);
}

function updateDependentButtons() {
  for (const testCase of CASES) {
    const button = document.querySelector(`[data-case="${testCase.id}"]`);
    button.disabled = !fixtureTemplate || (testCase.dependsOnAccepted && !acceptedFixture);
  }
}

function renderMatrix() {
  for (const testCase of CASES) {
    const card = document.createElement('section');
    card.className = 'case';
    card.dataset.caseCard = testCase.id;
    const heading = document.createElement('h3');
    heading.textContent = `Case ${testCase.id}: ${testCase.name}`;
    const expected = document.createElement('p');
    expected.textContent = `Expected: ${testCase.openCase ? 'OPEN spike-only observation' : testCase.expected}`;
    const status = document.createElement('p');
    status.className = 'status';
    status.textContent = 'NOT_RUN';
    status.dataset.state = 'NOT_RUN';
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.case = testCase.id;
    button.textContent = `Run Case ${testCase.id}`;
    button.addEventListener('click', () => executeCase(testCase));
    const output = document.createElement('pre');
    output.textContent = 'No result.';
    card.append(heading, expected, status, button, output);
    matrix.append(card);
  }
  updateDependentButtons();
}

async function loadFixture() {
  try {
    const response = await fetch(FIXTURE_PATH, { cache: 'no-store' });
    if (!response.ok) throw new Error(`Fixture load returned HTTP ${response.status}.`);
    fixtureTemplate = await response.json();
    fixtureStatus.textContent = 'Synthetic canonical fixture ready. Case 1 may now be run manually.';
  } catch (error) {
    fixtureStatus.textContent = `Fixture unavailable: ${safeError(error).message}`;
  }
  updateDependentButtons();
}

document.querySelector('#clear-results').addEventListener('click', () => {
  results.length = 0;
  acceptedFixture = null;
  copyOutput.textContent = 'No results yet.';
  for (const card of document.querySelectorAll('[data-case-card]')) {
    card.querySelector('.status').textContent = 'NOT_RUN';
    card.querySelector('.status').dataset.state = 'NOT_RUN';
    card.querySelector('pre').textContent = 'No result.';
  }
  updateDependentButtons();
});

document.querySelector('#copy-results').addEventListener('click', async () => {
  const sanitized = JSON.stringify({ spike_version: SPIKE_VERSION, results }, null, 2);
  copyOutput.textContent = sanitized;
  try {
    await navigator.clipboard.writeText(sanitized);
  } catch (error) {
    copyOutput.textContent = `${sanitized}\n\nClipboard unavailable; copy this block manually.`;
  }
});

renderMatrix();
loadFixture();
