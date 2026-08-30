export async function submitSurvey(response) {
  // No approved public endpoint exists. Keep this adapter local until deployment is reviewed.
  return { ok: true, status: 'demo', response_id: response.response_id };
}
