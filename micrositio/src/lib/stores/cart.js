import { writable, derived } from "svelte/store";

export const cart = writable([]);

export const cartTotal = derived(cart, ($cart) =>
  $cart.reduce((acc, p) => acc + p.qty * (p.price_sale ?? 0), 0)
);

// ⭐ ESTA ES LA EXPORTACIÓN QUE FALTA Y ROMPE LA APP ⭐
export const cartCount = derived(cart, ($cart) =>
  $cart.reduce((acc, p) => acc + (p.qty ?? 0), 0)
);

export function addToCart(product, qty = 1) {
  cart.update((items) => {
    const found = items.find((i) => i.sku === product.sku);
    if (found) {
      return items.map((i) =>
        i.sku === product.sku ? { ...i, qty: i.qty + qty } : i
      );
    }
    return [...items, { ...product, qty }];
  });
}

export function decreaseQty(sku) {
  cart.update((items) =>
    items.map((i) =>
      i.sku === sku ? { ...i, qty: Math.max(1, i.qty - 1) } : i
    )
  );
}

export function increaseQty(sku) {
  cart.update((items) =>
    items.map((i) =>
      i.sku === sku ? { ...i, qty: i.qty + 1 } : i
    )
  );
}

export function deleteFromCart(sku) {
  cart.update((items) => items.filter((i) => i.sku !== sku));
}

export function clearCartDirect() {
  cart.set([]);
}
