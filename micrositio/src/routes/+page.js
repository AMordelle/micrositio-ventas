export async function load({ fetch }) {
  const res = await fetch('/data/catalogo.json'); // cambia nombre si es otro
  if (!res.ok) {
    console.error("Error cargando catálogo:", res.statusText);
    return { productos: [] };
  }

  const productos = await res.json();
  return { productos };
}
