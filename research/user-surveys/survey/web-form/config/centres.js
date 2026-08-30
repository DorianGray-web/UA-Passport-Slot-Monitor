const taxonomyBase = '../../shared/taxonomy/';

export async function loadTaxonomies() {
	const [centresResponse, problemsResponse, channelsResponse] = await Promise.all([
		fetch(`${taxonomyBase}centres.json`),
		fetch(`${taxonomyBase}problem-categories.json`),
		fetch(`${taxonomyBase}notification-channels.json`),
	]);
	if (!centresResponse.ok || !problemsResponse.ok || !channelsResponse.ok) {
		throw new Error('taxonomy_load_failed');
	}
	return {
		centres: await centresResponse.json(),
		problems: await problemsResponse.json(),
		channels: await channelsResponse.json(),
	};
}
