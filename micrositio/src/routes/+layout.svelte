<script>
  import "../app.css";
  import FloatingWhatsApp from "$lib/components/FloatingWhatsApp.svelte";
  import CartFloating from "$lib/components/CartFloating.svelte";
</script>

<svelte:head>
  <meta name="theme-color" content="#ffffff" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    rel="stylesheet"
  >
</svelte:head>

<!-- CONTENIDO PRINCIPAL -->
<main class="page-wrapper">
  <slot />
</main>

<!-- COMPONENTES FLOATING (NO BLOQUEAN LA UI) -->
<div class="floating-area">
  <CartFloating />
  <FloatingWhatsApp />
</div>

<style>
  .page-wrapper {
    position: relative;
    z-index: 1; /* contenido por encima */
  }

  .floating-area {
    position: fixed;
    bottom: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    z-index: 999; /* por encima del contenido, pero NO bloquea */
    pointer-events: none; /* CLAVE: no intercepta clics a la página */
  }

  .floating-area :global(*) {
    pointer-events: auto; /* solo los botones flotantes SI aceptan clics */
  }
</style>
