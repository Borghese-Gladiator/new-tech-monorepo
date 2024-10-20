## Aug 13, 2023

# Svelte

First time writing Svelte code, though I've written a crap ton of React.

---

Svelte - free and open-source front-end JS component library. Components get compiled into small, efficient JavaScript modules that eliminate overhead traditionally associated with UI frameworks. You can build your entire app with Svelte (for example, using an application framework like SvelteKit, which this tutorial will cover), or you can add it incrementally to an existing codebase. You can also ship components as standalone packages that work anywhere.


- SvelteKit - utility to build Svelte apps built with Vite + Svelte
- Vite - modern build tool with dev server and Rollup bundling (built to to replace Webpack)


Features
- Compiled - runs way faster in browser by avoiding VirtualDOM
- Scoped CSS - CSS is component-scoped by default — no more style collisions or specificity wars. 
```
<script>
	import Nested from './Nested.svelte';
</script>

<p>These styles...</p>
<Nested />

<style>
	p {
		color: purple;
		font-family: 'Comic Sans MS', cursive;
		font-size: 2em;
	}
</style>
```
- Reactivity - Trigger efficient, granular updates by assigning to local variables. The compiler does the rest.
```javascript
<script>
	let count = 0;

	function handleClick() {
		count += 1;
	}
</script>

<button on:click={handleClick}>
	Clicked {count}
	{count === 1 ? 'time' : 'times'}
</button>
```

- Transitions

```
<script>
	import { quintOut } from 'svelte/easing';
	import { fade, draw, fly } from 'svelte/transition';
	import { expand } from './custom-transitions.js';
	import { inner, outer } from './shape.js';

	let visible = true;
</script>

{#if visible}
	<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 103 124">
		<g out:fade={{ duration: 200 }} opacity="0.2">
			<path
				in:expand={{ duration: 400, delay: 1000, easing: quintOut }}
				style="stroke: #ff3e00; fill: #ff3e00; stroke-width: 50;"
				d={outer}
			/>
			<path in:draw={{ duration: 1000 }} style="stroke:#ff3e00; stroke-width: 1.5" d={inner} />
		</g>
	</svg>

	<div class="centered" out:fly={{ y: -20, duration: 800 }}>
		{#each 'SVELTE' as char, i}
			<span in:fade|global={{ delay: 1000 + i * 150, duration: 800 }}>{char}</span>
		{/each}
	</div>
{/if}

<label>
	<input type="checkbox" bind:checked={visible} />
	toggle me
</label>

<link href="https://fonts.googleapis.com/css?family=Overpass:100,400" rel="stylesheet" />

<style>
	svg {
		width: 100%;
		height: 100%;
	}

	path {
		fill: white;
		opacity: 1;
	}

	label {
		position: absolute;
		top: 1em;
		left: 1em;
	}

	.centered {
		font-size: 20vw;
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		font-family: 'Overpass';
		letter-spacing: 0.12em;
		color: #676778;
		font-weight: 400;
	}

	.centered span {
		will-change: filter;
	}
</style>
```