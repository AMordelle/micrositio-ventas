<script>
  import { cart } from '$lib/stores/cart';
  import { onMount } from 'svelte';

  const phone = '522292645437';

  let message = '';
  let url = '';

  // Solo se ejecuta en cliente → evita SSR crash
  onMount(() => {
    // Reactividad manual al carrito (en cliente)
    const unsubscribe = cart.subscribe(($cart) => {
      const text =
        $cart.length === 0
          ? 'Hola, quiero hacer un pedido 😊'
          : 'Hola, quiero hacer este pedido:\n\n' +
            $cart
              .map((p) => `• ${p.name} (SKU ${p.sku}) x ${p.qty}`)
              .join('\n');

      message = encodeURIComponent(text);
      url = `https://wa.me/${phone}?text=${message}`;
    });

    return unsubscribe;
  });
</script>

<a
  href={url}
  target="_blank"
  rel="noreferrer"
  class="fixed bottom-6 right-6 bg-green-500 text-white px-5 py-3 rounded-full shadow-xl flex items-center gap-2 hover:bg-green-600 transition"
>
</a>
