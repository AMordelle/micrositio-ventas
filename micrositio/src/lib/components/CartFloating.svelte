<script>
  import { cart, cartTotal, decreaseQty, increaseQty, deleteFromCart, clearCartDirect } from '$lib/stores/cart';

  export let open = false;
  export let toggle;

  function confirmClear() {
    if (confirm("¿Vaciar todo el carrito?")) {
      clearCartDirect();
    }
  }
</script>

{#if open}
  <aside class="drawer">

    <header>
      <h2>Carrito</h2>
      <button on:click={toggle}>Cerrar</button>
    </header>

    <main>
      {#if $cart.length === 0}
        <p>No hay productos.</p>
      {:else}
        {#each $cart as item}
          <div class="item">
            <div>
              <p class="name">{item.name}</p>
              <p class="sku">SKU: {item.sku}</p>

              <div class="qty">
                <button on:click={() => decreaseQty(item.sku)}>-</button>
                <span>{item.qty}</span>
                <button on:click={() => increaseQty(item.sku)}>+</button>
              </div>
            </div>

            <div class="price-block">
              <p>${(item.price_sale * item.qty).toFixed(2)}</p>
              <button class="delete" on:click={() => deleteFromCart(item.sku)}>Eliminar</button>
            </div>
          </div>
        {/each}
      {/if}
    </main>

    <footer>
      <div class="total">
        <span>Total:</span>
        <span>${$cartTotal.toFixed(2)}</span>
      </div>

      <button class="clear" on:click={confirmClear}>Vaciar carrito</button>
    </footer>

  </aside>
{/if}

<style>
  .drawer {
    position: fixed;
    right: 0;
    top: 0;
    width: 90%;
    max-width: 380px;
    height: 100%;
    background: white;
    box-shadow: -2px 0 8px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
    padding: 14px;
    z-index: 9999;
  }
</style>
