<script>
  import { selectedCategory } from '$lib/stores/filters';

  export let categories = []; // ['Todas', 'Labiales', 'Perfumes', ...]

  const change = (event) => {
    selectedCategory.set(event.target.value);
  };
</script>

<div class="filters">
  <label>
    Categoría:
    <select on:change={change}>
      {#each categories as cat}
        <option value={cat}>{cat}</option>
      {/each}
    </select>
  </label>
</div>

<style>
  .filters {
    margin-bottom: 10px;
    font-size: 0.85rem;
    color: var(--text-muted);
  }

  select {
    margin-left: 6px;
    border-radius: 999px;
    border: 1px solid var(--border-soft);
    padding: 4px 10px;
    background: white;
  }
</style>
