export interface PhotographSummary {
	photograph_id: number;
	captured_at: string;
	image_path: string;
	keep_all: boolean;
	detection_count: number;
}

export interface Detection {
	tile_index: number;
	confidence: number;
	tile_url: string;
}

export interface PhotographDetail {
	photograph_id: number;
	captured_at: string;
	image_url: string;
	keep_all: boolean;
	detections: Detection[];
}

export interface Stats {
	total_photographs: number;
	total_detections: number;
}

export interface ShootResponse {
	photograph_id: number | null;
	message: string;
}

export async function getPhotographs(limit = 50): Promise<PhotographSummary[]> {
	const res = await fetch(`/api/photographs?limit=${limit}`);
	if (!res.ok) throw new Error('Failed to fetch photographs');
	return res.json();
}

export async function getPhotograph(id: number): Promise<PhotographDetail> {
	const res = await fetch(`/api/photographs/${id}`);
	if (!res.ok) throw new Error('Failed to fetch photograph');
	return res.json();
}

export async function getStats(): Promise<Stats> {
	const res = await fetch('/api/stats');
	if (!res.ok) throw new Error('Failed to fetch stats');
	return res.json();
}

export async function triggerShoot(): Promise<ShootResponse> {
	const res = await fetch('/api/shoot', { method: 'POST' });
	if (!res.ok) throw new Error('Failed to trigger capture');
	return res.json();
}

export function formatDate(isoString: string): string {
	const date = new Date(isoString);
	return date.toLocaleString();
}
