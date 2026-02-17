<script>
  import catalog from '$lib/data/catalog.json';
  import Header from '$lib/components/Header.svelte';
  import ProductCard from '$lib/components/ProductCard.svelte';
  import Filters from '$lib/components/Filters.svelte';
  import { selectedBrand, selectedCategory, searchQuery } from '$lib/stores/filters';

  function inferCategory(product) {
    const name = product.name.toLowerCase();

    if (name.includes('labial') || name.includes('boca') || name.includes('lip')) return 'Labiales';
    if (name.includes('base') || name.includes('corrector') || name.includes('polvo')) return 'Rostro';
    if (name.includes('máscara') || name.includes('mascara') || name.includes('pestañas')) return 'Ojos';
    if (name.includes('perfume') || name.includes('eau de parfum') || name.includes('eau de toilette')) return 'Fragancias';
    if (name.includes('jabón') || name.includes('jabones') || name.includes('barra')) return 'Cuerpo & Baño';
    if (name.includes('shampoo') || name.includes('cabello') || name.includes('sh ')) return 'Cabello';
    if (name.includes('crema') || name.includes('hidratante') || name.includes('loción')) return 'Cuidado de la piel';

    return 'Otros';
  }

  const enriched = catalog.map((p) => ({
    ...p,
    category: inferCategory(p)
  }));

  const categoriesSet = new Set(['Todas']);
  for (const p of enriched) categoriesSet.add(p.category);
  const categories = Array.from(categoriesSet);

  const PAGE_SIZE = 24;
  let currentPage = 1;

  $: brand = $selectedBrand;
  $: category = $selectedCategory;
  $: q = ($searchQuery || '').trim().toLowerCase();

  let prevBrand, prevCategory, prevQ;
  $: {
    if (brand !== prevBrand || category !== prevCategory || q !== prevQ) {
      currentPage = 1;
    }
    prevBrand = brand;
    prevCategory = category;
    prevQ = q;
  }

  $: filtered = enriched
    .filter((p) => (brand === 'Todas' ? true : p.brand === brand))
    .filter((p) => (category === 'Todas' ? true : p.category === category))
    .filter((p) => !q || p.name.toLowerCase().includes(q) || String(p.sku).toLowerCase().includes(q))
    .sort((a, b) => a.name.localeCompare(b.name, 'es'));

  let visible = [];
  $: totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  $: {
    const safePage = Math.min(Math.max(currentPage, 1), totalPages);
    currentPage = safePage;
    const start = (safePage - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    visible = filtered.slice(start, end);
  }

  function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  function labelForPage(page) {
    return page;
  }
</script>

<Header catalog={enriched} /> <!-- ← corregido -->

<main class="page">
  <section class="content">
    <div class="top-bar">
      <div>
        <h2>Productos</h2>
        <p class="summary">
          Mostrando {visible.length} de {filtered.length} productos
        </p>
      </div>

      <Filters {categories} />
    </div>

    <section class="grid">
      {#if visible.length === 0}
        <p>No se encontraron productos con los filtros actuales.</p>
      {:else}
        {#each visible as product}
          <ProductCard {product} />
        {/each}
      {/if}
    </section>

    {#if totalPages > 1}
      <nav class="pagination" aria-label="Paginación de productos">
        <button
          class="page-btn"
          on:click={() => goToPage(currentPage - 1)}
          disabled={currentPage === 1}
        >
          ⟵
        </button>

        {#each Array(totalPages) as _, i}
          {#if Math.abs(i + 1 - currentPage) <= 2 || i === 0 || i === totalPages - 1}
            <button
              class="page-btn {currentPage === i + 1 ? 'active' : ''}"
              on:click={() => goToPage(i + 1)}
            >
              {labelForPage(i + 1)}
            </button>
          {:else if
            (i === currentPage - 3 && currentPage > 3) ||
            (i === currentPage + 1 && currentPage < totalPages - 2)
          }
            <span class="page-ellipsis">…</span>
          {/if}
        {/each}

        <button
          class="page-btn"
          on:click={() => goToPage(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          ⟶
        </button>
      </nav>
    {/if}
  </section>
</main>


<style>
  .page {
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 14px 16px 40px;
  }

  .top-bar {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 16px;
    margin-bottom: 12px;
  }

  h2 {
    margin: 0;
    font-size: 1.1rem;
  }

  .summary {
    margin: 4px 0 0;
    font-size: 0.8rem;
    color: var(--text-muted);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    gap: 16px;
    margin-top: 8px;
    align-items: stretch;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    gap: 6px;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
    flex-wrap: wrap;
  }

  .page-btn {
    border-radius: 999px;
    border: 1px solid #e3d3c7;
    padding: 4px 10px;
    min-width: 32px;
    background: white;
    color: #6b5444;
    cursor: pointer;
    font-size: 0.82rem;
  }

  .page-btn.active {
    background: var(--primary);
    border-color: var(--primary);
    color: white;
  }

  .page-btn:disabled {
    background: #f0e5de;
    color: #aa9180;
    cursor: default;
  }

  .page-ellipsis {
    padding: 0 4px;
    color: #b79c8a;
  }

  @media (max-width: 720px) {
    .top-bar {
      flex-direction: column;
      align-items: stretch;
    }
  }
</style>
