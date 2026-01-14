<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getPhotographs,
		getStats,
		triggerShoot,
		formatDate,
		type PhotographSummary,
		type Stats
	} from '$lib/api';

	let photographs: PhotographSummary[] = $state([]);
	let stats: Stats | null = $state(null);
	let loading = $state(true);
	let capturing = $state(false);
	let error: string | null = $state(null);

	async function loadData() {
		try {
			[photographs, stats] = await Promise.all([getPhotographs(), getStats()]);
			error = null;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	}

	async function handleCapture() {
		capturing = true;
		try {
			const result = await triggerShoot();
			if (result.photograph_id) {
				await loadData();
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Capture failed';
		} finally {
			capturing = false;
		}
	}

	onMount(() => {
		loadData();
	});
</script>

<svelte:head>
	<title>Pi in the Sky</title>
</svelte:head>

<main>
	<h1>Pi in the Sky</h1>

	{#if error}
		<p class="error">{error}</p>
	{/if}

	<div class="stats">
		{#if stats}
			<span><strong>{stats.total_photographs}</strong> photographs</span>
			<span><strong>{stats.total_detections}</strong> detections</span>
		{/if}
		<button onclick={handleCapture} disabled={capturing}>
			{capturing ? 'Capturing...' : 'Capture Now'}
		</button>
	</div>

	<h2>Recent Photographs</h2>

	{#if loading}
		<p>Loading...</p>
	{:else if photographs.length === 0}
		<p>No photographs yet.</p>
	{:else}
		<div class="photo-grid">
			{#each photographs as photo}
				<a href="/photographs/{photo.photograph_id}">
					<img src="/images/{photo.image_path}" alt="Capture from {photo.captured_at}" />
					<div>{formatDate(photo.captured_at)}</div>
					<div>{photo.detection_count} detection{photo.detection_count !== 1 ? 's' : ''}</div>
				</a>
			{/each}
		</div>
	{/if}
</main>

<style>
	main {
		max-width: 1000px;
		margin: 0 auto;
		padding: var(--unit);
	}

	.error {
		color: red;
	}

	.stats {
		display: flex;
		gap: var(--unit);
		align-items: center;
		margin-bottom: var(--unit);
	}

	.stats button {
		font-family: var(--font);
		margin-left: auto;
	}

	.photo-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: var(--unit);
	}

	.photo-grid a {
		display: block;
		border: 1px solid #ccc;
		padding: calc(var(--unit) * 0.5);
	}

	.photo-grid img {
		width: 100%;
		height: 150px;
		object-fit: cover;
	}
</style>
