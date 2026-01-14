<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { getPhotograph, formatDate, type PhotographDetail } from '$lib/api';

	const GRID_COLS = 6;
	const GRID_ROWS = 3;
	const TOTAL_TILES = GRID_COLS * GRID_ROWS;

	let photo: PhotographDetail | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);

	function getBaseName(imagePath: string): string {
		return imagePath.replace(/\.[^.]+$/, '');
	}

	function getTileUrl(baseName: string, index: number): string {
		return `/images/${baseName}_${index.toString().padStart(2, '0')}.jpg`;
	}

	function getDetectionForTile(index: number): { confidence: number } | undefined {
		return photo?.detections.find((d) => d.tile_index === index);
	}

	onMount(async () => {
		const id = parseInt(page.params.id ?? '0');
		try {
			photo = await getPhotograph(id);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load photograph';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>{photo ? `Photo ${photo.photograph_id}` : 'Loading...'} - Pi in the Sky</title>
</svelte:head>

<main>
	<p><a href="/">← Back</a></p>

	{#if loading}
		<p>Loading...</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if photo}
		<h1>Photograph #{photo.photograph_id}</h1>
		<p>{formatDate(photo.captured_at)} — {photo.detections.length} detection{photo.detections.length !== 1 ? 's' : ''}</p>

		<h2>Full Image</h2>
		<img src={photo.image_url} alt="Capture" class="main-image" />

		<h2>Tiles</h2>
		<div class="tile-grid">
			{#each Array(TOTAL_TILES) as _, i}
				{@const detection = getDetectionForTile(i)}
				<div class="tile" class:has-detection={detection}>
					<img
						src={getTileUrl(getBaseName(photo.image_url.replace('/images/', '')), i)}
						alt="Tile {i}"
					/>
				</div>
			{/each}
		</div>
	{/if}
</main>

<style>
	main {
		max-width: 1000px;
		margin: 0 auto;
		padding: 1rem;
	}

	.error {
		color: red;
	}

	.main-image {
		max-width: 100%;
		height: auto;
	}

	.tile-grid {
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		gap: 0.5rem;
	}

	.tile {
		border: 1px solid #ccc;
		background: #eee;
		min-height: 80px;
	}

	.tile.has-detection {
		border: 2px solid green;
	}

	.tile img {
		width: 100%;
		height: auto;
		display: block;
	}

	.tile-label {
		padding: 0.25rem;
		font-size: 0.75rem;
		display: flex;
		justify-content: space-between;
	}

	.confidence {
		color: green;
		font-weight: bold;
	}
</style>
