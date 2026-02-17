export const formatPrice = (n) =>
  n?.toLocaleString('es-MX', {
    style: 'currency',
    currency: 'MXN'
  });
