<script>
  import { addToCart } from '$lib/stores/cart';

  export let product;

  // Cantidad local de la tarjeta
  let qty = 1;

  // Precio de venta seguro (fallback si algún producto viene raro)
  $: priceSale = product?.price_sale ?? product?.price_purchase ?? 0;

  function inc() {
    qty = Math.min(qty + 1, 99);
  }

  function dec() {
    qty = Math.max(qty - 1, 1);
  }

  function handleAdd() {
    addToCart(product, qty);
  }
</script>

<article class="card">
  <!-- Imagen -->
  <div class="image-wrap">
    <img src={product.image_url} alt={product.name} loading="lazy" />
  </div>

  <!-- Contenido principal -->
  <div class="content">
    <div class="text-block">
      <p class="brand">{product.brand}</p>
      <h3 class="name">{product.name}</h3>
      <p class="sku">SKU: {product.sku}</p>
    </div>

    <div class="bottom">
      <p class="price">
        ${priceSale.toFixed(2)}
      </p>

      <div class="actions">
        <div class="qty">
          <button type="button" on:click={dec}>-</button>
          <span>{qty}</span>
          <button type="button" on:click={inc}>+</button>
        </div>

        <button type="button" class="add" on:click={handleAdd}>
          Añadir
        </button>
      </div>
    </div>
  </div>
</article>

<style>
  .card {
    background: #ffffff;
    border-radius: 18px;
    border: 1px solid #f0e5de;
    padding: 10px 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    height: 100%;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
  }

  .image-wrap {
    width: 100%;
    height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  .content {
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .text-block {
    flex: 1;
  }

  .brand {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #a08672;
    margin: 0 0 2px;
  }

  .name {
    margin: 0;
    font-size: 0.86rem;
    font-weight: 600;
    color: #3f2e25;
    line-height: 1.25;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .sku {
    margin: 4px 0 0;
    font-size: 0.75rem;
    color: #9a8a80;
  }

  .bottom {
    margin-top: 8px;
  }

  .price {
    margin: 0 0 6px;
    font-size: 1rem;
    font-weight: 700;
    color: #3b2418;
  }

  .actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .qty {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid #e2d4cb;
    overflow: hidden;
    background: #f9f3ef;
    font-size: 0.8rem;
  }

  .qty button {
    width: 24px;
    height: 26px;
    border: none;
    background: transparent;
    cursor: pointer;
    font-weight: 600;
    color: #7b5b48;
  }

  .qty span {
    min-width: 22px;
    text-align: center;
    font-size: 0.8rem;
    color: #4a3a30;
  }

  .add {
    flex: 1;
    border: none;
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 0.8rem;
    font-weight: 600;
    background: #df4b44;
    color: white;
    cursor: pointer;
  }

  .add:hover {
    background: #c63f3a;
  }

  @media (max-width: 480px) {
    .card {
      border-radius: 16px;
    }
    .image-wrap {
      height: 140px;
    }
  }
</style>
