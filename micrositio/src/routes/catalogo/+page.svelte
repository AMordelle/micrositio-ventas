<script>
    import { products } from '$lib/stores/products';
    import { get } from 'svelte/store';
    import ProductCard from '$lib/components/ProductCard.svelte';
    export let url;

    let search = url.searchParams.get("search")?.toLowerCase() || "";
    let list = $products.filter(p =>
        p.name.toLowerCase().includes(search) ||
        p.sku.includes(search)
    );
</script>

<div class="p-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
    {#each list as product}
        <ProductCard {product} />
    {/each}
</div>
