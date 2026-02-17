<script>
  import { searchQuery } from '$lib/stores/filters';
  import { addToCart } from '$lib/stores/cart';

  // Catálogo completo enriquecido (desde Header)
  export let catalog = [];

  let q = '';
  let showList = false;
  let suggestions = [];
  let totalMatches = 0;

  // Estado de cantidades por SKU
  let quantities = {};

  // Sincronizar input con store global
  $: q = $searchQuery;

  function getQty(item) {
    const current = quantities[item.sku];
    return current ?? 1;
  }

  function setQty(item, value) {
    const v = Math.min(99, Math.max(1, value));
    quantities = { ...quantities, [item.sku]: v }; // reasignación → reactividad
  }

  // Debounce
  let debounce;
  function handleInput() {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      searchQuery.set(q);
      generateSuggestions();
    }, 160);
  }

  // Enter = Ver todos, Escape = cerrar dropdown
  function handleKeydown(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      clearTimeout(debounce);
      searchQuery.set(q);
      generateSuggestions();
      showAllResults();
    } else if (event.key === 'Escape') {
      showList = false;
    }
  }

  // Generar sugerencias (máx 5)
  function generateSuggestions() {
    const term = q.trim().toLowerCase();

    if (term.length < 2) {
      suggestions = [];
      totalMatches = 0;
      showList = false;
      return;
    }

    const matches = catalog.filter(
      (p) =>
        p.name.toLowerCase().includes(term) ||
        String(p.sku).toLowerCase().includes(term)
    );

    totalMatches = matches.length;
    suggestions = matches.slice(0, 5);
    showList = suggestions.length > 0;
  }

  function inc(item) {
    setQty(item, getQty(item) + 1);
  }

  function dec(item) {
    setQty(item, getQty(item) - 1);
  }

  function quickAdd(item) {
    addToCart(item, getQty(item));
  }

  // Botón "Ver todos los resultados"
  function showAllResults() {
    searchQuery.set(q);
    showList = false;

    // Scroll suave al catálogo
    if (typeof window !== 'undefined') {
      const section = document.querySelector('.grid');
      if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }
</script>

<div class="search-container">
  <input
    type="search"
    placeholder="Buscar productos..."
    bind:value={q}
    on:input={handleInput}
    on:keydown={handleKeydown}
    on:focus={() => (showList = suggestions.length > 0)}
  />

  {#if showList}
    <div class="dropdown">
      {#each suggestions as item (item.sku)}
        <div class="row">
          <!-- Imagen -->
          <img src={item.image_url} alt={item.name} class="img" />

          <!-- Información -->
          <div class="info">
            <p class="name">{item.name}</p>
            <p class="meta">{item.brand} • SKU {item.sku}</p>
            <p class="price">${(item.price_sale ?? 0).toFixed(2)}</p>
          </div>

          <!-- Controles -->
          <div class="actions">
            <div class="qty">
              <button type="button" on:click={() => dec(item)}>-</button>
              <!-- 👇 aquí ya usamos quantities directamente -->
              <span>{quantities[item.sku] ?? 1}</span>
              <button type="button" on:click={() => inc(item)}>+</button>
            </div>

            <button class="add" type="button" on:click={() => quickAdd(item)}>
              Añadir
            </button>
          </div>
        </div>
      {/each}

      <button class="show-all" type="button" on:click={showAllResults}>
        Ver todos los resultados ({totalMatches})
      </button>
    </div>
  {/if}
</div>

<style>
  .search-container {
    position: relative;
    width: 100%;
  }

  input {
    width: 100%;
    padding: 10px 14px;
    border-radius: 12px;
    border: 1px solid #d9c9bf;
    font-size: 0.9rem;
    background: #fff;
  }

  .dropdown {
    position: absolute;
    top: 110%;
    left: 0;
    width: 100%;
    background: #ffffff;
    border: 1px solid #e4d5cb;
    border-radius: 12px;
    box-shadow: 0 10px 20px rgba(0,0,0,0.08);
    z-index: 200;
    padding: 6px 0 0;
  }

  .row {
    display: flex;
    gap: 10px;
    padding: 8px 12px;
    border-bottom: 1px solid #f1e7df;
    align-items: center;
  }

  .img {
    width: 48px;
    height: 48px;
    object-fit: contain;
  }

  .info {
    flex: 1;
  }

  .name {
    margin: 0;
    font-size: 0.85rem;
    font-weight: 600;
    color: #3b2d25;
    line-height: 1.2;
  }

  .meta {
    font-size: 0.72rem;
    color: #9c8a80;
    margin: 2px 0 0;
  }

  .price {
    margin: 4px 0 0;
    font-size: 0.82rem;
    font-weight: 700;
    color: #3b2418;
  }

  .actions {
    display: flex;
    flex-direction: column;
    gap: 6px;
    align-items: flex-end;
  }

  .qty {
    display: flex;
    border-radius: 999px;
    border: 1px solid #e2d4cb;
    overflow: hidden;
    background: #f9f3ef;
    font-size: 0.75rem;
    align-items: center;
  }

  .qty button {
    width: 22px;
    height: 24px;
    border: none;
    background: transparent;
    cursor: pointer;
    font-weight: 600;
    color: #7b5b48;
  }

  .qty span {
    min-width: 20px;
    text-align: center;
    font-size: 0.75rem;
    color: #4a3a30;
  }

  .add {
    border: none;
    border-radius: 999px;
    padding: 4px 10px;
    font-size: 0.75rem;
    font-weight: 600;
    background: #df4b44;
    color: white;
    cursor: pointer;
  }

  .add:hover {
    background: #c43e39;
  }

  .show-all {
    width: 100%;
    padding: 12px;
    background: #f3ebe6;
    border: none;
    border-top: 1px solid #e4d5cb;
    font-size: 0.85rem;
    font-weight: 600;
    color: #7a5e4e;
    cursor: pointer;
    border-radius: 0 0 12px 12px;
  }

  .show-all:hover {
    background: #eaddd4;
  }
</style>
