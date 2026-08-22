const PROBE_VERSION = '1.0.0';
const MAX_PROBE_BODY_LENGTH = 4096;

function jsonOutput_(value) {
  return ContentService.createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}

function probeResponse_(method, requestId, contentType, contentLength) {
  return jsonOutput_({
    probe_version: PROBE_VERSION,
    probe_result: 'RECEIVED',
    method: method,
    request_id: requestId || null,
    content_type: contentType || null,
    content_length: contentLength,
    received_at: new Date().toISOString(),
    persistent_side_effect: false,
  });
}

function invalidProbe_(method, code) {
  return jsonOutput_({
    probe_version: PROBE_VERSION,
    probe_result: 'INVALID_PROBE',
    method: method,
    code: code,
    persistent_side_effect: false,
  });
}

function doGet(e) {
  const parameters = e && e.parameter ? e.parameter : {};
  if (parameters.probe_version !== PROBE_VERSION) {
    return invalidProbe_('GET', 'unsupported_probe_version');
  }
  return probeResponse_('GET', parameters.request_id, null, -1);
}

function doPost(e) {
  const postData = e && e.postData ? e.postData : null;
  const contents = postData && typeof postData.contents === 'string' ? postData.contents : '';
  if (!contents || contents.length > MAX_PROBE_BODY_LENGTH) {
    return invalidProbe_('POST', 'invalid_body_length');
  }

  let probe;
  try {
    probe = JSON.parse(contents);
  } catch (error) {
    return invalidProbe_('POST', 'invalid_json');
  }

  if (!probe || probe.probe_version !== PROBE_VERSION) {
    return invalidProbe_('POST', 'unsupported_probe_version');
  }

  return probeResponse_(
    'POST',
    typeof probe.request_id === 'string' ? probe.request_id : null,
    postData.type || null,
    contents.length
  );
}
