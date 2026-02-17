import { writable } from 'svelte/store';

export const products = writable([]);

export async function loadProducts() {
    const res = await fetch('/data/catalogo.json');
    const data = await res.json();
    products.set(data);
}
