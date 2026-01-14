<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { getPhotograph, formatDate, type PhotographDetail } from '$lib/api';

	let photo: PhotographDetail | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);

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
		<p>{formatDate(photo.captured_at)}</p>

		<img src={photo.image_url} alt="Capture" class="main-image" />

		<h2>Detections ({photo.detections.length})</h2>

		{#if photo.detections.length === 0}
			<p>No birds detected.</p>
		{:else}
			<div class="detections">
				{#each photo.detections as detection}
					<div class="detection">
						<img src={detection.tile_url} alt="Tile {detection.tile_index}" />
						<div>Tile {detection.tile_index} — {(detection.confidence * 100).toFixed(1)}%</div>
					</div>
				{/each}
			</div>
		{/if}
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

	.detections {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.detection {
		border: 1px solid #ccc;
		padding: 0.5rem;
	}

	.detection img {
		width: 150px;
		height: 150px;
		object-fit: cover;
	}
</style>
