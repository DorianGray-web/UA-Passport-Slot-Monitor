const SPIKE_VERSION = '3.0.0';
const SUPPORTED_CONTRACT_VERSION = '2.0.0';
const MAX_BODY_LENGTH = 16384;
const EXPERIMENTAL_LOCK_TIMEOUT_MS = 3000;
const SPREADSHEET_ID_PROPERTY = 'SPIKE_SPREADSHEET_ID';
const SPIKE_SHEET_NAME = 'ContractValidationSpike';
const SPIKE_HEADERS = ['response_id', 'payload_sha256'];

function jsonOutput_(value) {
  return ContentService.createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}

function canonicalOutcome_(outcome, diagnostic) {
  const response = {
    spike_version: SPIKE_VERSION,
    outcome: outcome,
    envelope_status: 'EXPERIMENTAL_NOT_A_PRODUCTION_CONTRACT',
  };
  if (diagnostic) response.diagnostic = diagnostic;
  return response;
}

function spikeOnlyResult_(spikeResult, diagnostic) {
  const response = {
    spike_version: SPIKE_VERSION,
    spike_result: spikeResult,
    result_scope: 'SPIKE_ONLY_NON_CANONICAL',
  };
  if (diagnostic) response.diagnostic = diagnostic;
  return response;
}

function doPost(e) {
  const postData = e && e.postData ? e.postData : null;
  const rawBody = postData && typeof postData.contents === 'string'
    ? postData.contents
    : '';
  const parameters = e && e.parameter ? e.parameter : {};
  const control = {
    forceTemporaryFailure: parameters.spike_control === 'temporary_failure',
  };

  let response;
  try {
    response = handleRawRequest_(rawBody, control, appsScriptDependencies_());
  } catch (error) {
    response = canonicalOutcome_('TEMPORARY_FAILURE', {
      code: 'unexpected_spike_failure',
      persistence_effect: 'not_established',
    });
  }
  return jsonOutput_(response);
}

function handleRawRequest_(rawBody, control, dependencies) {
  if (typeof rawBody !== 'string' || rawBody.length === 0 || rawBody.length > MAX_BODY_LENGTH) {
    return canonicalOutcome_('INVALID_REQUEST', {
      code: 'invalid_body_length',
      persistence_effect: 'none',
    });
  }

  let payload;
  try {
    payload = JSON.parse(rawBody);
  } catch (error) {
    return canonicalOutcome_('INVALID_REQUEST', {
      code: 'malformed_json',
      persistence_effect: 'none',
    });
  }

  if (
    isPlainObject_(payload)
    && typeof payload.contract_version === 'string'
    && payload.contract_version !== SUPPORTED_CONTRACT_VERSION
  ) {
    return canonicalOutcome_('UNSUPPORTED_CONTRACT', {
      code: 'unsupported_contract_version',
      persistence_effect: 'none',
    });
  }

  const validationErrors = validateCanonicalPayload_(payload);
  if (validationErrors.length > 0) {
    return canonicalOutcome_('INVALID_REQUEST', {
      code: 'schema_validation_failed',
      errors: validationErrors.slice(0, 12),
      persistence_effect: 'none',
      validator_scope: 'SPIKE_SCHEMA_KEYWORD_SUBSET',
    });
  }

  if (control && control.forceTemporaryFailure) {
    return canonicalOutcome_('TEMPORARY_FAILURE', {
      code: 'controlled_transient_before_persistence',
      persistence_effect: 'none',
      control_scope: 'SPIKE_ONLY',
    });
  }

  const canonicalJson = canonicalJson_(payload);
  const payloadHash = dependencies.sha256(canonicalJson);

  try {
    return dependencies.withLock(function () {
      const existing = dependencies.findByResponseId(payload.response_id);
      if (existing) {
        if (existing.payloadHash === payloadHash) {
          return canonicalOutcome_('DUPLICATE_ACCEPTED', {
            code: 'equivalent_identity_already_recorded',
            physical_records_for_response_id: existing.count,
            persistence_effect: 'none',
          });
        }
        return spikeOnlyResult_('OPEN_IDENTITY_CONTENT_CONFLICT', {
          code: 'same_response_id_non_equivalent_content',
          physical_records_for_response_id: existing.count,
          persistence_effect: 'none',
        });
      }

      dependencies.appendRecord(payload.response_id, payloadHash);
      return canonicalOutcome_('ACCEPTED', {
        code: 'validated_identity_hash_recorded',
        physical_records_for_response_id: 1,
        persistence_effect: 'one_disposable_record',
      });
    });
  } catch (error) {
    if (error && error.spikeCode === 'experimental_lock_unavailable') {
      return canonicalOutcome_('TEMPORARY_FAILURE', {
        code: 'experimental_lock_unavailable',
        persistence_effect: 'none',
        experimental_lock_timeout_ms: EXPERIMENTAL_LOCK_TIMEOUT_MS,
      });
    }
    return canonicalOutcome_('TEMPORARY_FAILURE', {
      code: 'experimental_storage_unavailable',
      persistence_effect: 'not_established',
    });
  }
}

function validateCanonicalPayload_(payload) {
  return validateSchemaNode_(CANONICAL_SURVEY_RESPONSE_SCHEMA, payload, '$', CANONICAL_SURVEY_RESPONSE_SCHEMA);
}

function validateSchemaNode_(schema, value, path, rootSchema) {
  if (!schema || typeof schema !== 'object') return [];
  if (schema.$ref) {
    const resolved = resolveLocalRef_(rootSchema, schema.$ref);
    return resolved
      ? validateSchemaNode_(resolved, value, path, rootSchema)
      : [validationError_(path, 'unsupported_schema_reference')];
  }

  let errors = [];
  if (schema.anyOf) {
    const matched = schema.anyOf.some(function (candidate) {
      return validateSchemaNode_(candidate, value, path, rootSchema).length === 0;
    });
    if (!matched) errors.push(validationError_(path, 'any_of_failed'));
    return errors;
  }

  if (schema.allOf) {
    schema.allOf.forEach(function (candidate) {
      errors = errors.concat(validateSchemaNode_(candidate, value, path, rootSchema));
    });
  }

  if (Object.prototype.hasOwnProperty.call(schema, 'const') && !deepEqual_(value, schema.const)) {
    errors.push(validationError_(path, 'const_mismatch'));
  }
  if (schema.enum && !schema.enum.some(function (candidate) { return deepEqual_(value, candidate); })) {
    errors.push(validationError_(path, 'unknown_value'));
  }

  if (schema.type && !matchesType_(value, schema.type)) {
    errors.push(validationError_(path, 'wrong_type'));
    return errors;
  }

  if (typeof value === 'string') {
    if (schema.minLength !== undefined && value.length < schema.minLength) {
      errors.push(validationError_(path, 'too_short'));
    }
    if (schema.maxLength !== undefined && value.length > schema.maxLength) {
      errors.push(validationError_(path, 'too_long'));
    }
    if (schema.pattern && !(new RegExp(schema.pattern)).test(value)) {
      errors.push(validationError_(path, 'pattern_mismatch'));
    }
    if (schema.format === 'uuid' && !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(value)) {
      errors.push(validationError_(path, 'invalid_uuid'));
    }
    if (schema.format === 'date-time' && !isRfc3339DateTime_(value)) {
      errors.push(validationError_(path, 'invalid_date_time'));
    }
  }

  if (typeof value === 'number') {
    if (schema.minimum !== undefined && value < schema.minimum) errors.push(validationError_(path, 'below_minimum'));
    if (schema.maximum !== undefined && value > schema.maximum) errors.push(validationError_(path, 'above_maximum'));
  }

  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) errors.push(validationError_(path, 'too_few_items'));
    if (schema.maxItems !== undefined && value.length > schema.maxItems) errors.push(validationError_(path, 'too_many_items'));
    if (schema.uniqueItems && hasDuplicateItems_(value)) errors.push(validationError_(path, 'duplicate_items'));
    if (schema.items) {
      value.forEach(function (item, index) {
        errors = errors.concat(validateSchemaNode_(schema.items, item, path + '[' + index + ']', rootSchema));
      });
    }
    if (schema.contains) {
      const containsMatch = value.some(function (item, index) {
        return validateSchemaNode_(schema.contains, item, path + '[' + index + ']', rootSchema).length === 0;
      });
      if (!containsMatch) errors.push(validationError_(path, 'contains_failed'));
    }
  }

  if (isPlainObject_(value)) {
    const properties = schema.properties || {};
    (schema.required || []).forEach(function (requiredKey) {
      if (!Object.prototype.hasOwnProperty.call(value, requiredKey)) {
        errors.push(validationError_(path + '.' + requiredKey, 'required'));
      }
    });
    Object.keys(properties).forEach(function (key) {
      if (Object.prototype.hasOwnProperty.call(value, key)) {
        errors = errors.concat(validateSchemaNode_(properties[key], value[key], path + '.' + key, rootSchema));
      }
    });
    if (schema.additionalProperties === false) {
      Object.keys(value).forEach(function (key) {
        if (!Object.prototype.hasOwnProperty.call(properties, key)) {
          errors.push(validationError_(path + '.' + key, 'additional_property'));
        }
      });
    }
  }

  if (schema.if) {
    const conditionMatches = validateSchemaNode_(schema.if, value, path, rootSchema).length === 0;
    if (conditionMatches && schema.then) {
      errors = errors.concat(validateSchemaNode_(schema.then, value, path, rootSchema));
    } else if (!conditionMatches && schema.else) {
      errors = errors.concat(validateSchemaNode_(schema.else, value, path, rootSchema));
    }
  }
  return deduplicateErrors_(errors);
}

function resolveLocalRef_(rootSchema, reference) {
  if (typeof reference !== 'string' || reference.indexOf('#/') !== 0) return null;
  return reference.slice(2).split('/').reduce(function (current, part) {
    const key = part.replace(/~1/g, '/').replace(/~0/g, '~');
    return current && Object.prototype.hasOwnProperty.call(current, key) ? current[key] : null;
  }, rootSchema);
}

function validationError_(path, code) { return { path: path, code: code }; }

function deduplicateErrors_(errors) {
  const seen = {};
  return errors.filter(function (error) {
    const key = error.path + '|' + error.code;
    if (seen[key]) return false;
    seen[key] = true;
    return true;
  });
}

function matchesType_(value, expected) {
  const types = Array.isArray(expected) ? expected : [expected];
  return types.some(function (type) {
    if (type === 'null') return value === null;
    if (type === 'array') return Array.isArray(value);
    if (type === 'object') return isPlainObject_(value);
    if (type === 'integer') return typeof value === 'number' && Number.isInteger(value);
    if (type === 'number') return typeof value === 'number' && Number.isFinite(value);
    return typeof value === type;
  });
}

function isPlainObject_(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }

function isRfc3339DateTime_(value) {
  return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/.test(value) && !Number.isNaN(Date.parse(value));
}

function hasDuplicateItems_(items) {
  const seen = {};
  return items.some(function (item) {
    const key = canonicalJson_(item);
    if (seen[key]) return true;
    seen[key] = true;
    return false;
  });
}

function deepEqual_(left, right) { return canonicalJson_(left) === canonicalJson_(right); }

function canonicalJson_(value) {
  if (Array.isArray(value)) return '[' + value.map(canonicalJson_).join(',') + ']';
  if (isPlainObject_(value)) {
    return '{' + Object.keys(value).sort().map(function (key) {
      return JSON.stringify(key) + ':' + canonicalJson_(value[key]);
    }).join(',') + '}';
  }
  return JSON.stringify(value);
}

function appsScriptDependencies_() {
  return {
    sha256: sha256Hex_,
    withLock: withExperimentalScriptLock_,
    findByResponseId: findByResponseId_,
    appendRecord: appendRecord_,
  };
}

function sha256Hex_(value) {
  const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, value, Utilities.Charset.UTF_8);
  return digest.map(function (byte) {
    return ((byte + 256) % 256).toString(16).padStart(2, '0');
  }).join('');
}

function withExperimentalScriptLock_(callback) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(EXPERIMENTAL_LOCK_TIMEOUT_MS)) {
    const error = new Error('Experimental ScriptLock was not acquired.');
    error.spikeCode = 'experimental_lock_unavailable';
    throw error;
  }
  try {
    return callback();
  } finally {
    lock.releaseLock();
  }
}

function disposableSheet_() {
  const spreadsheetId = PropertiesService.getScriptProperties().getProperty(SPREADSHEET_ID_PROPERTY);
  if (!spreadsheetId) throw new Error('Spike spreadsheet configuration is missing.');
  const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
  let sheet = spreadsheet.getSheetByName(SPIKE_SHEET_NAME);
  if (!sheet) sheet = spreadsheet.insertSheet(SPIKE_SHEET_NAME);
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, SPIKE_HEADERS.length).setValues([SPIKE_HEADERS]);
  } else {
    const headers = sheet.getRange(1, 1, 1, SPIKE_HEADERS.length).getValues()[0];
    if (!deepEqual_(headers, SPIKE_HEADERS)) throw new Error('Unexpected disposable Sheet headers.');
  }
  return sheet;
}

function findByResponseId_(responseId) {
  const sheet = disposableSheet_();
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return null;
  const rows = sheet.getRange(2, 1, lastRow - 1, SPIKE_HEADERS.length).getValues();
  const matches = rows.filter(function (row) { return row[0] === responseId; });
  if (matches.length === 0) return null;
  return { payloadHash: matches[0][1], count: matches.length };
}

function appendRecord_(responseId, payloadHash) {
  disposableSheet_().appendRow([responseId, payloadHash]);
}
