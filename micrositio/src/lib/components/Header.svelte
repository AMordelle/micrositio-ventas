<script>
  import SearchBar from "$lib/components/SearchBar.svelte";
  import { cartCount } from "$lib/stores/cart";
  import { selectedBrand } from "$lib/stores/filters";

  export let catalog = [];

  const brands = ["Todas", "Natura", "Avon", "Casa & Estilo"];

  const selectBrand = (b) => {
    selectedBrand.set(b);
  };
</script>

<header class="header">
  <div class="header-container">

    <!-- TITULO + CARRITO -->
    <div class="row">
      <div class="title">
        <h1>Catálogo de Ruth</h1>
        <p>Productos Natura, Avon y Casa & Estilo.</p>
      </div>

      <!-- BOTÓN DEL CARRITO -->
      <a href="/carrito" class="cart-btn" aria-label="Carrito de compras">
        <!-- ICONO PROFESIONAL NUEVO -->
        <svg
          width="26" height="26"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="9" cy="21" r="1"></circle>
          <circle cx="20" cy="21" r="1"></circle>
          <path d="M1 1h4l2.5 13h13l2-8H6"></path>
        </svg>

        {#if $cartCount > 0}
          <span class="badge">{$cartCount}</span>
        {/if}
      </a>
    </div>

    <!-- BUSCADOR -->
    <div class="search-wrapper">
      <SearchBar {catalog} />
    </div>

    <!-- FILTROS DE MARCA -->
    <div class="brands">
      {#each brands as brand}
        <button
          class:selected={brand === $selectedBrand}
          on:click={() => selectBrand(brand)}
        >
          {brand}
        </button>
      {/each}
    </div>

  </div>
</header>

<style>
  .header {
    background: linear-gradient(135deg, #f7eadd, #faf6f3);
    padding: 16px 0;
    border-bottom: 1px solid #e9dfda;
    position: sticky;
    top: 0;
    z-index: 50;
  }

  .header-container {
    max-width: var(--max-width);
    margin: 0 auto;
    width: 100%;
    padding: 0 16px;
  }

  .row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .title h1 {
    margin: 0;
    font-size: 1.38rem;
    font-weight: 700;
  }

  .title p {
    margin: 2px 0 0;
    font-size: 0.85rem;
    color: #866f63;
  }

  /* CARRITO */
  .cart-btn {
    position: relative;
    width: 46px;
    height: 46px;
    background: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    cursor: pointer;
    border: 1px solid #eee;
  }

  .cart-btn svg {
    color: #5b4637;
    transition: 0.2s ease-in-out;
  }

  .cart-btn:hover svg {
    color: #8a6a54;
  }

  .badge {
    position: absolute;
    top: -6px;
    right: -6px;
    background: #df4b44;
    color: white;
    font-size: 0.7rem;
    padding: 1px 6px;
    border-radius: 999px;
    font-weight: 600;
  }

  /* BUSCADOR */
  .search-wrapper {
    margin-top: 12px;
    margin-bottom: 10px;
    width: 100%;
  }

  /* FILTROS */
  .brands {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 10px;
  }

  .brands button {
    border: 1px solid #e8dcd6;
    background: white;
    color: #6b5a52;
    padding: 6px 12px;
    border-radius: 14px;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.18s ease;
  }

  .brands button.selected {
    background: #df4b44;
    color: white;
    border-color: #df4b44;
  }

  /* RESPONSIVE */
  @media (max-width: 480px) {
    .row {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    .cart-btn {
      align-self: flex-end;
      margin-top: -36px;
    }

    .title h1 {
      font-size: 1.25rem;
    }
  }
</style>
