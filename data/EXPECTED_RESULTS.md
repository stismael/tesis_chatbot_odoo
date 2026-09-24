# Resultados esperados - Datos sintéticos Chatbot

Estos casos ancla deben verificarse después de ejecutar la generación de datos
desde **Ajustes > Chatbot Test Data > Generar datos de prueba**.

Semilla: `random.seed(2026)`

---

## Caso 1: Factura pagada

| Campo | Valor esperado |
|-------|----------------|
| Cliente | Comercial Andina S.A. |
| Factura | INV/2026/00001 |
| Total | USD 1.250,00 |
| Estado | Publicada y pagada (`payment_state = paid`) |

**Consulta chatbot sugerida:** *¿Cuál es el total de la factura INV/2026/00001?*

---

## Caso 2: Factura vencida sin pagar

| Campo | Valor esperado |
|-------|----------------|
| Cliente | Moto Racing Cuenca |
| Factura | INV/2026/00002 |
| Total | USD 840,00 |
| Estado | Publicada, vencida y no pagada |

**Consulta chatbot sugerida:** *¿Qué facturas están vencidas del cliente Moto Racing Cuenca?*

---

## Caso 3: Producto con stock (filtro)

| Campo | Valor esperado |
|-------|----------------|
| Producto | Filtro de aceite M01 |
| Código | FIL-M01 |
| Stock disponible | ≥ 25 (positivo) |

**Consulta chatbot sugerida:** *¿Cuántas unidades hay del producto FIL-M01?*

---

## Caso 4: Producto con stock (casco)

| Campo | Valor esperado |
|-------|----------------|
| Producto | Casco Integral Negro |
| Código | CAS-001 |
| Stock disponible | ≥ 25 (positivo) |

**Consulta chatbot sugerida:** *¿Hay stock del Casco Integral Negro?*

---

## Caso 5: Vendedor asignado al cliente

| Campo | Valor esperado |
|-------|----------------|
| Cliente | Comercial Andina S.A. |
| Vendedor | Andrea Villafuerte |
| Email vendedor | andrea.villafuerte@demo-motos.ec |
| Teléfono vendedor | +593 99 801 1101 |

**Consulta chatbot sugerida:** *¿Quién es el vendedor asignado a Comercial Andina S.A.?*

---

## Caso 6: Vendedor de cliente con factura vencida

| Campo | Valor esperado |
|-------|----------------|
| Cliente | Moto Racing Cuenca |
| Vendedor | Diego Salinas |
| Email vendedor | diego.salinas@demo-motos.ec |
| Teléfono vendedor | +593 99 801 1102 |

**Consulta chatbot sugerida:** *¿Cuál es el contacto del vendedor de Moto Racing Cuenca?*

---

## Caso 7: Cotización con varios productos

| Campo | Valor esperado |
|-------|----------------|
| Cliente | Comercial Andina S.A. |
| Origen | COT-2026-MULTI-01 |
| Estado | Cotización (presupuesto) |
| Líneas | 4 productos distintos |

**Consulta chatbot sugerida:** *¿Qué productos incluye la cotización COT-2026-MULTI-01?*

---

## Caso 8: Factura con varios productos

| Campo | Valor esperado |
|-------|----------------|
| Cliente | Comercial Andina S.A. |
| Pedido | PV-2026-MULTI-01 |
| Factura | INV/2026/00003 |
| Líneas | 5 productos distintos |
| Estado | Publicada y pagada |

**Consulta chatbot sugerida:** *¿Cuántos productos tiene la factura INV/2026/00003?*

---

## Volúmenes aproximados generados

| Entidad | Cantidad |
|---------|----------|
| Contactos totales | ~115 |
| Clientes | ~90 |
| Prospectos | ~15 |
| Vendedores | 5 |
| Proveedores | ~10 |
| Categorías producto | 5 |
| Productos almacenables | ~80 |
| Pedidos de venta | ~950 |
| Cotizaciones (borrador) | ~85 |
| Líneas de venta | ~2500+ |
| Facturas cliente | ≥ 600 |
| Facturas/pedidos multiproducto | ~45% |
| Stock por producto | ≥ 25 (sin ceros ni negativos) |
| Pedidos cancelados | ~10% |
| Presupuestos no confirmados | ~25% |

---

## Identificación de registros generados

Los datos usan nombres comerciales realistas (empresas, personas, productos).
Referencia interna en campo `ref`: prefijo `DEMO-CUST-`, `DEMO-SUPP-` (no visible en listados principales).
Marcador técnico oculto: partner inactivo con `ref = _INTERNAL_DEMO_LOADED_2026`.
Origen de pedidos: `PV-2026-XXXX`.
