<script>
  import {
    cart,
    cartTotal,
    increaseQty,
    decreaseQty,
    deleteFromCart,
    clearCartDirect
  } from "$lib/stores/cart";

  $: items = $cart;
  $: total = $cartTotal;

  function confirmarVaciado() {
    if (confirm("¿Seguro que deseas vaciar el carrito?")) {
      clearCartDirect();
    }
  }

  function eliminarItem(sku) {
    if (confirm("¿Eliminar este producto del carrito?")) {
      deleteFromCart(sku);
    }
  }

  function enviarWhatsApp() {
    if (!items.length) return;

    let mensaje = "¡Hola! Me gustaría hacer un pedido:%0A%0A";

    for (const item of items) {
      mensaje += `• ${item.name} (SKU ${item.sku})%0A  Cantidad: ${item.qty}%0A  Subtotal: $${(
        item.qty * item.price_sale
      ).toFixed(2)}%0A%0A`;
    }

    mensaje += `TOTAL: $${total.toFixed(2)}%0A¿Está disponible?`;

    const numero = "521##########";
    window.open(`https://wa.me/${numero}?text=${mensaje}`, "_blank");
  }
</script>

<div class="carrito">
  <h1 class="titulo">
    <span>🛒 Carrito</span>
    <a href="/" class="volver">← Volver</a>
  </h1>

  {#if !items.length}
    <p class="vacio">Tu carrito está vacío.</p>

  {:else}

    <div class="lista">
      {#each items as item}
        <article class="item-card">
          
          <!-- Imagen -->
          <div class="img-wrap">
            <img src={item.image_url} alt={item.name} />
          </div>

          <!-- Info -->
          <div class="info">
            <h3>{item.name}</h3>
            <p class="sku">SKU: {item.sku}</p>

            <!-- Controles de cantidad -->
            <div class="qty">
              <button on:click={() => decreaseQty(item.sku)}>-</button>
              <span>{item.qty}</span>
              <button on:click={() => increaseQty(item.sku)}>+</button>
            </div>
          </div>

          <!-- Precio y eliminar -->
          <div class="right">
            <p class="subtotal">${(item.qty * item.price_sale).toFixed(2)}</p>

            <button
              class="delete"
              on:click={() => eliminarItem(item.sku)}
              title="Eliminar"
            >
              🗑️
            </button>
          </div>

        </article>
      {/each}
    </div>

    <footer class="totales">
      <div class="total-right">
        <span>Total:</span>
        <strong>${total.toFixed(2)}</strong>
      </div>

      <button class="wsp" on:click={enviarWhatsApp}>
        Enviar por WhatsApp
      </button>

      <button class="vaciar" on:click={confirmarVaciado}>
        Vaciar carrito
      </button>
    </footer>
  {/if}
</div>

<style>
  .carrito {
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 20px;
  }

  .titulo {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
    font-size: 1.6rem;
  }

  .volver {
    font-size: 0.9rem;
    background: #eee;
    padding: 6px 14px;
    border-radius: 10px;
    text-decoration: none;
    color: #444;
    font-weight: 500;
  }

  .lista {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .item-card {
    display: flex;
    gap: 18px;
    background: white;
    border-radius: 18px;
    padding: 16px;
    box-shadow: 0 3px 6px rgba(0,0,0,0.05);
    border: 1px solid #f1eae4;
    align-items: center;
  }

  .img-wrap {
    width: 120px;
    height: 120px;
    flex-shrink: 0;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .img-wrap img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  .info {
    flex: 1;
  }

  .info h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: #3d2f26;
  }

  .sku {
    margin-top: 4px;
    color: #8b7b71;
    font-size: 0.8rem;
  }

  .qty {
    margin-top: 10px;
    display: flex;
    gap: 8px;
    align-items: center;
    border-radius: 999px;
    padding: 4px 10px;
    background: #f7f2ef;
    border: 1px solid #e7d8d1;
  }

  .qty button {
    width: 26px;
    height: 26px;
    border: none;
    background: transparent;
    cursor: pointer;
    font-size: 1rem;
    font-weight: bold;
    color: #7a5b48;
  }

  .qty span {
    width: 24px;
    text-align: center;
    font-weight: 600;
  }

  .right {
    text-align: right;
  }

  .subtotal {
    margin: 0 0 10px;
    font-size: 1.1rem;
    font-weight: 700;
    color: #3b2418;
  }

  .delete {
    background: #ffecec;
    border: 1px solid #e9c7c7;
    border-radius: 10px;
    padding: 6px 10px;
    cursor: pointer;
    transition: 0.2s;
  }

  .delete:hover {
    background: #ffd0d0;
  }

  .totales {
    margin-top: 28px;
    padding-top: 14px;
    border-top: 1px solid #eee;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .total-right {
    font-size: 1.4rem;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }

  .wsp {
    background: #25D366;
    color: white;
    padding: 14px;
    border-radius: 12px;
    border: none;
    font-weight: bold;
    cursor: pointer;
    font-size: 1.1rem;
  }

  .vaciar {
    background: #ddd;
    padding: 12px;
    border-radius: 12px;
    border: none;
    cursor: pointer;
    font-size: 0.95rem;
  }

  @media (max-width: 600px) {
    .item-card {
      flex-direction: column;
      align-items: flex-start;
    }
    .right {
      align-self: flex-end;
    }
  }
</style>
