<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children()}

<style>
	:global(:root) {
		--font: "Helvetica Neue", "Helvetica", "Arial", sans-serif;
		--unit: 16px;
	}
</style>
