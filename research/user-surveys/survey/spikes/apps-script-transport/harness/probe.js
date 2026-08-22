const PROBE_VERSION = '1.0.0';
const endpointInput = document.querySelector('#endpoint');
const result = document.querySelector('#result');

function endpointUrl() {
  const url = new URL(endpointInput.value);
  if (url.protocol !== 'https:' || url.hostname !== 'script.google.com' || !url.pathname.endsWith('/exec')) {
    throw new Error('Enter an HTTPS script.google.com web-app URL ending in /exec.');
  }
  return url;
}

function safeError(error) {
  return {
    name: error instanceof Error ? error.name : 'Error',
    message: error instanceof Error ? error.message : 'Probe failed',
  };
}

async function runProbe(kind) {
  const requestId = crypto.randomUUID();
  const startedAt = new Date().toISOString();
  const started = performance.now();
  const evidence = {
    probe_version: PROBE_VERSION,
    probe_kind: kind,
    request_id: requestId,
    started_at: startedAt,
    persistence_expected: false,
  };

  try {
    const url = endpointUrl();
    const isGet = kind === 'get-cors';
    const mode = kind === 'post-no-cors' ? 'no-cors' : 'cors';
    const options = { method: isGet ? 'GET' : 'POST', mode, redirect: 'follow' };

    if (isGet) {
      url.searchParams.set('probe_version', PROBE_VERSION);
      url.searchParams.set('request_id', requestId);
    } else {
      options.headers = { 'Content-Type': 'text/plain;charset=UTF-8' };
      options.body = JSON.stringify({
        probe_version: PROBE_VERSION,
        request_id: requestId,
        sent_at: startedAt,
        marker: 'non_persistent_transport_probe',
      });
    }

    const response = await fetch(url, options);
    evidence.duration_ms = Math.round(performance.now() - started);
    evidence.response = {
      type: response.type,
      status: response.status,
      ok: response.ok,
      redirected: response.redirected,
      final_origin: response.url ? new URL(response.url).origin : null,
      content_type: response.headers.get('content-type'),
    };

    if (response.type === 'opaque') {
      evidence.interpretation = 'Dispatch attempted; browser security prevents observing receipt or response.';
    } else {
      const body = await response.text();
      try {
        evidence.probe_response = JSON.parse(body);
      } catch (error) {
        evidence.response_parse = 'non_json_response';
      }
      evidence.interpretation = response.ok
        ? 'Browser received a readable response; inspect probe_response before drawing feasibility conclusions.'
        : 'Browser received a readable non-success HTTP response.';
    }
  } catch (error) {
    evidence.duration_ms = Math.round(performance.now() - started);
    evidence.error = safeError(error);
    evidence.interpretation = 'No readable probe result was established. This may be URL, access, redirect, network, or CORS behavior.';
  }

  result.textContent = JSON.stringify(evidence, null, 2);
}

for (const button of document.querySelectorAll('[data-probe]')) {
  button.addEventListener('click', () => runProbe(button.dataset.probe));
}
