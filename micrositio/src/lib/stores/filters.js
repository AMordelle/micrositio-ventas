import { writable } from 'svelte/store';

export const selectedBrand = writable('Todas'); // 'Todas', 'Natura', 'Avon', 'Casa & Estilo'
export const selectedCategory = writable('Todas'); // generadas dinámicamente
export const searchQuery = writable(''); // texto libre
