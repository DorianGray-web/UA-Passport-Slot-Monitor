const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const spikeRoot = path.resolve(__dirname, '..');
const fixture = JSON.parse(fs.readFileSync(path.join(spikeRoot, 'fixtures', 'valid-survey-response.json'), 'utf8'));
const source = [
  fs.readFileSync(path.join(spikeRoot, 'ContractSnapshot.gs'), 'utf8'),
  fs.readFileSync(path.join(spikeRoot, 'Code.gs'), 'utf8'),
  'globalThis.__spike = { handleRawRequest_, validateCanonicalPayload_ };',
].join('\n');
const context = {
  console, Date, JSON, Number, Object, RegExp, Error,
  Utilities: {
    DigestAlgorithm: { SHA_256: 'SHA_256' },
    Charset: { UTF_8: 'UTF_8' },
    computeDigest(_algorithm, value) {
      return [...crypto.createHash('sha256').update(value, 'utf8').digest()].map((byte) => byte > 127 ? byte - 256 : byte);
    },
  },
};
vm.createContext(context);
new vm.Script(source, { filename: 'apps-script-contract-validation.gs' }).runInContext(context);
const { handleRawRequest_, validateCanonicalPayload_ } = context.__spike;
const clone = (value) => JSON.parse(JSON.stringify(value));

function dependencies() {
  const records = new Map();
  let writes = 0;
  return {
    records,
    get writes() { return writes; },
    sha256(value) { return crypto.createHash('sha256').update(value, 'utf8').digest('hex'); },
    withLock(callback) { return callback(); },
    findByResponseId(responseId) {
      const payloadHash = records.get(responseId);
      return payloadHash ? { payloadHash, count: 1 } : null;
    },
    appendRecord(responseId, payloadHash) { writes += 1; records.set(responseId, payloadHash); },
  };
}

assert.equal(validateCanonicalPayload_(fixture).length, 0);
const deps = dependencies();
const rawFixture = JSON.stringify(fixture);
assert.equal(handleRawRequest_(rawFixture, {}, deps).outcome, 'ACCEPTED');
assert.equal(deps.writes, 1);
assert.equal(handleRawRequest_(rawFixture, {}, deps).outcome, 'DUPLICATE_ACCEPTED');
assert.equal(deps.writes, 1);
assert.equal(handleRawRequest_('{"broken":', {}, dependencies()).outcome, 'INVALID_REQUEST');

const missingNullable = clone(fixture);
delete missingNullable.answers.appointment_urgency;
assert.equal(handleRawRequest_(JSON.stringify(missingNullable), {}, dependencies()).outcome, 'INVALID_REQUEST');
const invalidUuid = clone(fixture);
invalidUuid.response_id = 'not-a-uuid';
assert.equal(handleRawRequest_(JSON.stringify(invalidUuid), {}, dependencies()).outcome, 'INVALID_REQUEST');
const invalidTaxonomy = clone(fixture);
invalidTaxonomy.answers.centre_ids = ['nonexistent_centre'];
assert.equal(handleRawRequest_(JSON.stringify(invalidTaxonomy), {}, dependencies()).outcome, 'INVALID_REQUEST');
const wrongType = clone(fixture);
wrongType.answers.problem_category_ids = 'none';
assert.equal(handleRawRequest_(JSON.stringify(wrongType), {}, dependencies()).outcome, 'INVALID_REQUEST');
const unsupported = clone(fixture);
unsupported.contract_version = '999.0.0';
assert.equal(handleRawRequest_(JSON.stringify(unsupported), {}, dependencies()).outcome, 'UNSUPPORTED_CONTRACT');
const transientDeps = dependencies();
assert.equal(handleRawRequest_(rawFixture, { forceTemporaryFailure: true }, transientDeps).outcome, 'TEMPORARY_FAILURE');
assert.equal(transientDeps.writes, 0);
const lockFailureDeps = dependencies();
lockFailureDeps.withLock = () => {
  const error = new Error('controlled lock failure');
  error.spikeCode = 'experimental_lock_unavailable';
  throw error;
};
assert.equal(handleRawRequest_(rawFixture, {}, lockFailureDeps).outcome, 'TEMPORARY_FAILURE');
assert.equal(lockFailureDeps.writes, 0);
const changed = clone(fixture);
changed.answers.early_testing_interest = 'yes';
const conflict = handleRawRequest_(JSON.stringify(changed), {}, deps);
assert.equal(conflict.outcome, undefined);
assert.equal(conflict.spike_result, 'OPEN_IDENTITY_CONTENT_CONFLICT');
assert.equal(deps.writes, 1);
console.log('Spike 3 contract-validation tests passed.');
