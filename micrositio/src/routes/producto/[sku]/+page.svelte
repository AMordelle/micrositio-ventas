<script>
    import { products } from '$lib/stores/products';
    import { get } from 'svelte/store';
    import { addToCart } from '$lib/stores/cart';
    export let params;

    const product = get(products).find(p => p.sku === params.sku);
</script>

{#if product}
<div class="p-6">
    <img src={product.image_url}
         class="w-full rounded shadow" alt={`Imagen del producto ${product.name}`} />

    <h1 class="text-xl font-bold mt-4">{product.name}</h1>

    <p class="text-gray-400 text-sm mt-1">SKU: {product.sku}</p>

    <p class="text-pink-600 font-bold text-3xl mt-4">
        ${product.price_sale?.toFixed(2)}
    </p>

    <button
        class="bg-pink-600 text-white px-6 py-3 rounded mt-4"
        on:click={() => addToCart(product)}>
        Agregar al carrito
    </button>
</div>
{/if}
