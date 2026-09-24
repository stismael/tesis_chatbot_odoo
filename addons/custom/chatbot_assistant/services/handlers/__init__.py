from . import factura
from . import stock
from . import ventas
from . import vendedor

HANDLER_MAP = {
    "consultar_factura": factura.handle,
    "consultar_stock": stock.handle,
    "consultar_ventas_cliente": ventas.handle,
    "consultar_vendedor_cliente": vendedor.handle,
}
