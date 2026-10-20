# -*- coding: utf-8 -*-
import random
import re
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Marcador interno (no visible en listados comerciales)
MARKER_REF = '_INTERNAL_DEMO_LOADED_2026'
SEED = 2026

TARGET_CUSTOMERS = 90
TARGET_PROSPECTS = 15
TARGET_SUPPLIERS = 10
TARGET_SALE_ORDERS = 350
TARGET_INVOICES = 600
MIN_STOCK_QTY = 25

# Nombres ficticios pero realistas — Ecuador / Latinoamérica
ANCHOR_CUSTOMERS = [
    ('Comercial Andina S.A.', 'comercial.andina@andina-motors.ec', 'Quito', 'Av. Amazonas N24-120', 'andrea.villafuerte@demo-motos.ec'),
    ('Moto Racing Cuenca', 'ventas@motoracingcuenca.ec', 'Cuenca', 'Av. Solano 045 y Remigio Crespo', 'diego.salinas@demo-motos.ec'),
]

SALESPEOPLE = [
    ('Andrea Villafuerte', 'andrea.villafuerte@demo-motos.ec', '+593 99 801 1101'),
    ('Diego Salinas', 'diego.salinas@demo-motos.ec', '+593 99 801 1102'),
    ('Patricia Morales', 'patricia.morales@demo-motos.ec', '+593 99 801 1103'),
    ('Roberto Cevallos', 'roberto.cevallos@demo-motos.ec', '+593 99 801 1104'),
    ('Lucía Espinosa', 'lucia.espinosa@demo-motos.ec', '+593 99 801 1105'),
]

CUSTOMER_COMPANIES = [
    'Distribuidora El Oriente Cía. Ltda.',
    'Autopartes Guerrero',
    'Motos del Valle S.A.',
    'Repuestos Automotrices Pérez',
    'Comercial Zambrano Hermanos',
    'Importadora Pacífico Motor',
    'Talleres Unidos del Austro',
    'Distribuidora Norte Motor',
    'Accesorios Vélez & Asociados',
    'Comercializadora Delta Motor',
    'Grupo Mecánica Integral',
    'Repuestos La Floresta',
    'Motopartes del Litoral',
    'Autodistribution Center S.A.',
    'Servicios Mecánicos ProMoto',
    'Distribuidora Sur Equipos',
    'Motores y Repuestos Cía. Ltda.',
    'Comercial El Progreso Motor',
    'Distribuidora Centro Motos',
    'Repuestos Express Ambato',
    'Autopartes del Pacífico',
    'Comercial Riobamba Motor',
    'Taller Mecánico Integral S.A.',
    'Importadora Andina Parts',
    'Distribuidora Loja Motor',
    'Comercial Manta Repuestos',
    'Motopartes Ecuador S.A.',
    'Repuestos Universales Cía. Ltda.',
    'Comercial Galápagos Motor',
    'Distribuidora Ibarra Parts',
    'Autorepuestos del Valle',
    'Comercial Santo Domingo Motor',
    'Motos y Accesorios Plus',
    'Repuestos Premium Ecuador',
    'Distribuidora Machala Motor',
    'Comercial Esmeraldas Parts',
    'Autopartes Latacunga S.A.',
    'Motopartes Cotopaxi',
    'Comercial Portoviejo Motor',
    'Repuestos del Austro Cía. Ltda.',
    'Distribuidora Manabí Motor',
    'Comercial Tulcán Repuestos',
    'Autopartes Chimborazo',
    'Motos del Litoral S.A.',
    'Comercial Babahoyo Parts',
    'Repuestos Milagro Motor',
    'Distribuidora Quevedo S.A.',
    'Comercial Latacunga Motor',
    'Autopartes Santo Domingo',
    'Motopartes Cayambe Cía. Ltda.',
    'Comercial Durán Repuestos',
    'Repuestos Machala Express',
    'Distribuidora Esmeraldas Motor',
]

CUSTOMER_PERSONS = [
    'Juan Carlos Mendoza',
    'María Fernanda Salazar',
    'Luis Alberto Torres',
    'Patricia Elena Vásquez',
    'Roberto Enrique Castro',
    'Ana Lucía Herrera',
    'Diego Armando Romero',
    'Carmen Rosa Delgado',
    'Fernando Javier Quintero',
    'Gabriela Isabel Morales',
    'Ricardo Antonio Suárez',
    'Verónica Alejandra Paredes',
    'Héctor Manuel Bravo',
    'Sandra Milena Ortiz',
    'Carlos Eduardo Vega',
    'Daniela Paola Ríos',
    'Miguel Ángel Paredes',
    'Laura Beatriz Cordero',
    'Andrés Felipe Guzmán',
    'Valentina Sofía Mora',
    'Jorge Luis Intriago',
    'Paola Andrea Cabrera',
    'Francisco Javier León',
    'Adriana Marcela Peña',
    'Sebastián Andrés Viteri',
    'Natalia Isabel Aguirre',
    'Pablo Esteban Ruiz',
    'Camila Alejandra Mendieta',
    'Oscar Daniel Alarcón',
    'Karina Elizabeth Noboa',
    'Raúl Enrique Palacios',
    'Silvia Margarita Cevallos',
    'Iván Mauricio Salgado',
    'Jessica Paola Benítez',
    'Mauricio Antonio López',
    'Elena Cristina Figueroa',
    'Tomás Eduardo Sarango',
    'Lucía Fernanda Arroyo',
    'Emilio José Zambrano',
    'Rosa Amelia Espinosa',
]

COMPANY_PREFIXES = [
    'Comercial', 'Distribuidora', 'Importadora', 'Autopartes', 'Motopartes',
    'Repuestos', 'Talleres', 'Servicios', 'Grupo', 'Centro',
]

COMPANY_CORES = [
    'Andino', 'Pacífico', 'Austro', 'Norte', 'Sur', 'Valle', 'Sierra',
    'Litoral', 'Central', 'Integral', 'Express', 'Premium', 'Global',
]

COMPANY_SUFFIXES = [
    'Motor S.A.', 'Repuestos Cía. Ltda.', 'Motos S.A.', 'Automotriz',
    'Parts Ecuador', 'Motopartes', 'de Motos', 'Motor Plus',
]

PERSON_FIRST_NAMES = [
    'Carlos', 'María', 'Luis', 'Ana', 'José', 'Patricia', 'Roberto', 'Laura',
    'Diego', 'Gabriela', 'Fernando', 'Carmen', 'Andrés', 'Daniela', 'Pablo',
    'Valentina', 'Miguel', 'Silvia', 'Raúl', 'Jessica', 'Iván', 'Paola',
]

PERSON_LAST_NAMES = [
    'Mendoza', 'Salazar', 'Torres', 'Vásquez', 'Castro', 'Herrera', 'Romero',
    'Delgado', 'Quintero', 'Morales', 'Suárez', 'Paredes', 'Bravo', 'Ortiz',
    'Vega', 'Ríos', 'Guzmán', 'Mora', 'Cordero', 'León', 'Peña', 'Ruiz',
    'Alarcón', 'Noboa', 'Palacios', 'Cevallos', 'Benítez', 'López', 'Zambrano',
]

SUPPLIER_COMPANIES = [
    'Importadora Pacífico S.A.',
    'Motopartes del Sur Cía. Ltda.',
    'Distribuidora Andina de Repuestos',
    'Lubricantes Continental Ecuador',
    'Accesorios MotoPro S.A.',
    'Proveedora Nacional de Motos',
    'Importadora Euro Parts Ecuador',
    'Distribuidora Mayorista Motor',
    'Lubricantes Andinos S.A.',
    'Repuestos Industriales del Ecuador',
]

STREETS = [
    'Av. 10 de Agosto', 'Calle Sucre', 'Av. Francisco de Orellana',
    'Av. de las Américas', 'Calle Larga', 'Av. Universitaria',
    'Av. Colón', 'Calle Benigno Malo', 'Av. Huaynacapac',
    'Av. Maldonado', 'Calle Bolívar', 'Av. Kennedy',
]

PRODUCT_CATEGORIES = [
    'Repuestos Motocicletas',
    'Accesorios y Seguridad',
    'Lubricantes y Filtros',
    'Herramientas Taller',
    'Equipamiento Rider',
]

PRODUCT_NAMES = [
    ('Pastillas freno delanteras', 'PAST-DEL-001'),
    ('Cadena transmisión 520', 'CAD-520-001'),
    ('Bujía iridium NGK', 'BUJ-NGK-001'),
    ('Espejo retrovisor universal', 'ESP-UNI-001'),
    ('Manillar aluminio 22mm', 'MAN-ALU-001'),
    ('Grip antideslizante par', 'GRP-ANT-001'),
    ('Kit embrague completo', 'KEM-001'),
    ('Radiador aceite universal', 'RAD-ACE-001'),
    ('Protector motor aluminio', 'PRM-001'),
    ('Luces LED faro H4', 'LED-H4-001'),
    ('Porta celular moto', 'PCM-001'),
    ('Baúl lateral 35 litros', 'BAU-35L-001'),
    ('Chaqueta impermeable touring', 'CHQ-IMP-001'),
    ('Guantes touring cuero', 'GUA-TOU-001'),
    ('Botas adventure talla 42', 'BOT-ADV-042'),
    ('Aceite motor 10W40 1L', 'ACE-10W40-1L'),
    ('Filtro aire deportivo', 'FLA-DEP-001'),
    ('Batería gel 12V 7Ah', 'BAT-GEL-7AH'),
    ('Disco freno ondulado 320mm', 'DIS-ONL-320'),
    ('Amortiguador trasero OEM', 'AMO-TRAS-001'),
    ('Kit reparación pinchazo', 'KRP-001'),
    ('Soporte GPS manillar', 'SGP-001'),
    ('Intercomunicador bluetooth', 'INT-BT-001'),
    ('Cubrepiernas térmico', 'CPT-001'),
    ('Mochila hidratación 2L', 'MOC-HID-2L'),
    ('Candado U antirobo', 'CAN-U-001'),
    ('Cubre moto impermeable L', 'CMI-L-001'),
    ('Slider frame protección', 'SLD-FRM-001'),
    ('Palanca freno corta CNC', 'PLF-CNC-001'),
    ('Pedal cambios ajustable', 'PDC-AJU-001'),
    ('Protector tanque transparente', 'PRT-TAN-001'),
    ('Visor casco ahumado', 'VIS-AHU-001'),
    ('Cinta reflectiva 5m', 'CFL-5M-001'),
    ('Kit limpieza cadena', 'KLC-001'),
    ('Lubricante cadena 400ml', 'LUB-CAD-400'),
    ('Medidor presión neumáticos', 'MPN-001'),
    ('Inflador CO2 portátil', 'INF-CO2-001'),
    ('Soporte botella agua manillar', 'SBA-001'),
    ('Funda asiento gel', 'FAS-GEL-001'),
    ('Elevador central moto 500kg', 'ELV-500-001'),
    ('Caballetes mantenimiento par', 'CAB-MAN-001'),
    ('Torquímetro digital 1/4', 'TRQ-DIG-001'),
    ('Multímetro automotriz', 'MUL-AUT-001'),
    ('Llave torque 1/4 set', 'LLT-001'),
    ('Extractor filtro aceite', 'EFA-001'),
    ('Bomba vacío frenos', 'BVF-001'),
    ('Kit pastillas traseras', 'PAST-TRAS-001'),
    ('Cable acelerador universal', 'CAB-ACE-001'),
    ('Rodamiento rueda delantera', 'ROD-RDD-001'),
    ('Kit cadena y piñones', 'KCP-520-001'),
    ('Filtro combustible inline', 'FLC-INL-001'),
    ('Bomba de combustible', 'BOM-COM-001'),
    ('Carburador universal 28mm', 'CAR-28-001'),
    ('Bobina encendido CDI', 'BOB-CDI-001'),
    ('Relé arranque 12V', 'REL-ARR-001'),
    ('Regulador voltaje alternador', 'REG-VOL-001'),
    ('Manómetro aceite digital', 'MAN-ACE-001'),
    ('Tapón aceite magnético', 'TAP-MAG-001'),
    ('Junta culata kit completo', 'JUN-CUL-001'),
    ('Retén horquilla 43mm', 'RET-HOR-001'),
    ('Aceite horquilla 10W 1L', 'ACE-HOR-1L'),
    ('Líquido frenos DOT4 500ml', 'LIQ-FRE-500'),
    ('Manguera freno acero', 'MAN-FRE-001'),
    ('Caliper delantero reparación', 'CAL-DEL-001'),
    ('Disco freno flotante 310mm', 'DIS-FLO-310'),
    ('Pinza freno trasera', 'PIN-TRAS-001'),
    ('Zapatillas freno traseras', 'ZAP-TRAS-001'),
    ('Kit rodamientos dirección', 'KRD-001'),
    ('Corona 42 dientes', 'COR-42-001'),
    ('Piñón ataque 15 dientes', 'PIN-15-001'),
    ('Tensor cadena automático', 'TEN-CAD-001'),
    ('Guardabarros delantero universal', 'GUA-DEL-001'),
    ('Parabrisas touring ajustable', 'PAR-TOU-001'),
    ('Deflector viento clip-on', 'DEF-VIE-001'),
    ('Asideros pasajero cromados', 'ASI-PAS-001'),
    ('Reposapiés piloto ajustables', 'REP-PIL-001'),
    ('Estriberas aluminio racing', 'EST-RAC-001'),
    ('Puños calefactables 22mm', 'PUI-CAL-001'),
    ('Intermitentes LED par', 'INT-LED-001'),
    ('Luz stop LED adicional', 'LUZ-STOP-001'),
]


def _slug_email(name):
    base = re.sub(r'[^a-z0-9]+', '.', name.lower())
    base = re.sub(r'\.+', '.', base).strip('.')
    return f'{base[:40]}@demo-motos.ec'


class ChatbotTestDataGenerator(models.AbstractModel):
    _name = 'chatbot.test.data.generator'
    _description = 'Generador de datos sintéticos para chatbot'

    @api.model
    def generate_all(self):
        """Genera datos sintéticos deterministas con nombres realistas."""
        if self._is_already_generated():
            raise UserError(_(
                'Los datos de demostración ya fueron generados en esta base. '
                'Use el script reset-database.ps1 para recrear la base.'
            ))

        random.seed(SEED)
        env = self.env

        env['res.partner'].create({
            'name': 'Registro interno demo',
            'ref': MARKER_REF,
            'company_type': 'company',
            'active': False,
        })

        company = env.company
        self._ensure_usd(company)
        salespeople = self._create_salespeople()
        categories = self._create_categories()
        partners = self._create_partners(salespeople)
        products = self._create_products(categories)
        self._create_stock(products)
        orders = self._create_sale_orders(partners, products)
        self._create_anchor_cases(partners, products, orders)
        self._create_multi_product_cases(partners, products)
        self._create_additional_invoices(partners, products)
        # Reponer stock tras ventas/entregas para que ningún producto quede en 0 o negativo
        self._ensure_positive_stock(products)

        return True

    @api.model
    def _is_already_generated(self):
        return bool(self.env['res.partner'].with_context(active_test=False).search_count([
            ('ref', '=', MARKER_REF),
        ]))

    @api.model
    def _ensure_usd(self, company):
        usd = self.env.ref('base.USD', raise_if_not_found=False)
        if usd and company.currency_id != usd:
            company.currency_id = usd

    @api.model
    def _create_salespeople(self):
        sales_group = self.env.ref('sales_team.group_sale_salesman')
        Users = self.env['res.users'].sudo()
        company = self.env.company
        salespeople = Users

        for name, login, phone in SALESPEOPLE:
            existing = Users.with_context(active_test=False).search([('login', '=', login)], limit=1)
            if existing:
                existing.write({'name': name, 'phone': phone, 'active': True})
                salespeople |= existing
                continue
            salespeople |= Users.create({
                'name': name,
                'login': login,
                'email': login,
                'phone': phone,
                'password': 'Demo2026!',
                'groups_id': [(6, 0, [sales_group.id])],
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
            })
        return salespeople

    @api.model
    def _next_customer_name(self, used_names, company_pool, person_pool):
        if company_pool:
            name = company_pool.pop()
        elif person_pool:
            name = person_pool.pop()
        else:
            for _ in range(50):
                if random.random() < 0.55:
                    name = (
                        f'{random.choice(COMPANY_PREFIXES)} '
                        f'{random.choice(COMPANY_CORES)} '
                        f'{random.choice(COMPANY_SUFFIXES)}'
                    )
                else:
                    name = (
                        f'{random.choice(PERSON_FIRST_NAMES)} '
                        f'{random.choice(PERSON_LAST_NAMES)} '
                        f'{random.choice(PERSON_LAST_NAMES)}'
                    )
                if name not in used_names:
                    break
            else:
                name = f'Contacto Comercial {len(used_names) + 1:03d}'
        used_names.add(name)
        return name

    @api.model
    def _build_order_lines(self, saleable, force_multi=False):
        saleable_list = list(saleable)
        if not saleable_list:
            return []

        if force_multi:
            line_count = random.randint(3, min(6, len(saleable_list)))
        else:
            roll = random.random()
            if roll < 0.40:
                line_count = random.randint(3, min(6, len(saleable_list)))
            elif roll < 0.70:
                line_count = random.randint(2, min(4, len(saleable_list)))
            else:
                line_count = 1

        chosen = random.sample(saleable_list, line_count)
        lines = []
        for prod in chosen:
            lines.append((0, 0, {
                'product_id': prod.product_variant_id.id,
                'product_uom_qty': random.randint(1, 8),
                'price_unit': prod.list_price,
            }))
        return lines

    @api.model
    def _create_categories(self):
        Category = self.env['product.category']
        categories = Category
        for name in PRODUCT_CATEGORIES:
            existing = Category.search([('name', '=', name)], limit=1)
            categories |= existing or Category.create({'name': name})
        return categories

    @api.model
    def _create_partners(self, salespeople):
        cities = ['Quito', 'Guayaquil', 'Cuenca', 'Ambato', 'Loja', 'Manta', 'Riobamba']
        partners = self.env['res.partner']
        country_ec = self.env.ref('base.ec').id
        by_login = {user.login: user for user in salespeople}

        for name, email, city, street, salesperson_login in ANCHOR_CUSTOMERS:
            partners |= self.env['res.partner'].create({
                'name': name,
                'ref': f'DEMO-CUST-{len(partners) + 1:03d}',
                'company_type': 'company',
                'email': email,
                'phone': '+593 99 210 0101',
                'street': street,
                'city': city,
                'country_id': country_ec,
                'customer_rank': 1,
                'user_id': by_login[salesperson_login].id,
            })

        company_pool = CUSTOMER_COMPANIES[:]
        random.shuffle(company_pool)
        person_pool = CUSTOMER_PERSONS[:]
        random.shuffle(person_pool)
        used_names = {p.name for p in partners}

        while len(partners) < TARGET_CUSTOMERS:
            city = random.choice(cities)
            street = f'{random.choice(STREETS)} {random.randint(100, 999)}'
            phone = f'+593 {random.choice(["2", "4", "7"])}{random.randint(1000000, 9999999)}'
            name = self._next_customer_name(used_names, company_pool, person_pool)
            is_company = (
                name.endswith('S.A.')
                or 'Cía.' in name
                or 'Ltda.' in name
                or 'Distribuidora' in name
                or 'Comercial' in name
                or 'Importadora' in name
                or 'Motopartes' in name
                or 'Repuestos' in name
                or 'Autopartes' in name
                or 'Talleres' in name
                or 'Servicios' in name
                or 'Grupo' in name
                or 'Centro' in name
            )

            partners |= self.env['res.partner'].create({
                'name': name,
                'ref': f'DEMO-CUST-{len(partners) + 1:03d}',
                'company_type': 'company' if is_company else 'person',
                'email': _slug_email(name),
                'phone': phone,
                'street': street,
                'city': city,
                'country_id': country_ec,
                'customer_rank': 1,
                'user_id': random.choice(salespeople).id,
            })

        prospects = self.env['res.partner']
        for _ in range(TARGET_PROSPECTS):
            city = random.choice(cities)
            street = f'{random.choice(STREETS)} {random.randint(100, 999)}'
            phone = f'+593 {random.choice(["2", "4", "7"])}{random.randint(1000000, 9999999)}'
            name = self._next_customer_name(used_names, company_pool, person_pool)
            is_company = random.random() < 0.45
            prospects |= self.env['res.partner'].create({
                'name': name,
                'ref': f'DEMO-PROS-{len(prospects) + 1:03d}',
                'company_type': 'company' if is_company else 'person',
                'email': _slug_email(name),
                'phone': phone,
                'street': street,
                'city': city,
                'country_id': country_ec,
                'customer_rank': 0,
                'supplier_rank': 0,
            })

        suppliers = self.env['res.partner']
        supplier_names = SUPPLIER_COMPANIES[:TARGET_SUPPLIERS]
        for i, name in enumerate(supplier_names):
            city = random.choice(cities)
            suppliers |= self.env['res.partner'].create({
                'name': name,
                'ref': f'DEMO-SUPP-{i + 1:02d}',
                'company_type': 'company',
                'email': _slug_email(name),
                'phone': f'+593 4 {random.randint(200, 999)}{random.randint(1000, 9999)}',
                'street': f'{random.choice(STREETS)} {random.randint(10, 400)}',
                'city': city,
                'country_id': country_ec,
                'supplier_rank': 1,
            })

        return partners | prospects | suppliers

    @api.model
    def _create_products(self, categories):
        Product = self.env['product.template']
        products = Product

        anchors = [
            ('Filtro de aceite M01', 'FIL-M01', 18.50),
            ('Casco Integral Negro', 'CAS-001', 120.00),
        ]
        for name, code, price in anchors:
            products |= Product.create({
                'name': name,
                'default_code': code,
                'type': 'consu',
                'is_storable': True,
                'categ_id': categories[2].id,
                'list_price': price,
                'standard_price': round(price * 0.6, 2),
                'sale_ok': True,
                'purchase_ok': True,
            })

        for i, (pname, code) in enumerate(PRODUCT_NAMES):
            cat = categories[i % len(categories)]
            price = round(random.uniform(8, 280), 2)
            products |= Product.create({
                'name': pname,
                'default_code': code,
                'type': 'consu',
                'is_storable': True,
                'categ_id': cat.id,
                'list_price': price,
                'standard_price': round(price * random.uniform(0.45, 0.7), 2),
                'sale_ok': True,
                'purchase_ok': random.random() > 0.25,
            })

        return products

    @api.model
    def _get_warehouse(self):
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not warehouse:
            warehouse = self.env['stock.warehouse'].create({
                'name': 'Almacén Central Quito',
                'code': 'ALMC',
                'company_id': self.env.company.id,
            })
        return warehouse

    @api.model
    def _create_stock(self, products):
        """Carga inicial de inventario con cantidades positivas."""
        warehouse = self._get_warehouse()
        StockQuant = self.env['stock.quant'].sudo()
        for tmpl in products:
            product = tmpl.product_variant_id
            if product.default_code == 'CAS-001':
                qty = 120
            elif product.default_code == 'FIL-M01':
                qty = 85
            else:
                qty = random.randint(40, 200)

            StockQuant._update_available_quantity(
                product, warehouse.lot_stock_id, qty
            )
        return warehouse

    @api.model
    def _ensure_positive_stock(self, products):
        """Garantiza stock disponible > 0 tras confirmar ventas y entregas."""
        warehouse = self._get_warehouse()
        StockQuant = self.env['stock.quant'].sudo()
        location = warehouse.lot_stock_id

        for tmpl in products:
            product = tmpl.product_variant_id
            # free_qty contempla reservas; evita stock negativo o cero
            available = product.free_qty if hasattr(product, 'free_qty') else product.qty_available
            if available >= MIN_STOCK_QTY:
                continue
            delta = int(MIN_STOCK_QTY - available) + random.randint(10, 60)
            if delta > 0:
                StockQuant._update_available_quantity(product, location, float(delta))

    @api.model
    def _create_sale_orders(self, partners, products):
        customers = partners.filtered(lambda p: p.customer_rank > 0 and p.ref != MARKER_REF)
        saleable = products.filtered('sale_ok')
        SaleOrder = self.env['sale.order']
        orders = SaleOrder

        for i in range(TARGET_SALE_ORDERS):
            partner = random.choice(customers)
            state_roll = random.random()
            order_lines = self._build_order_lines(saleable)

            order = SaleOrder.create({
                'partner_id': partner.id,
                'user_id': partner.user_id.id,
                'origin': f'PV-2026-{i + 1:04d}',
                'order_line': order_lines,
            })

            if state_roll < 0.10:
                order.action_cancel()
            elif state_roll < 0.35:
                pass
            elif order.order_line:
                order.action_confirm()
            orders |= order

        return orders

    @api.model
    def _create_multi_product_cases(self, partners, products):
        """Cotizaciones y ventas ancla con varios productos."""
        andina = partners.filtered(lambda p: p.name == 'Comercial Andina S.A.')[:1]
        moto = partners.filtered(lambda p: p.name == 'Moto Racing Cuenca')[:1]
        saleable = products.filtered('sale_ok')
        if len(saleable) < 4:
            return

        multi_products = saleable.filtered(
            lambda p: p.default_code in ('CAS-001', 'FIL-M01', 'PAST-DEL-001', 'ACE-10W40-1L', 'GUA-TOU-001')
        ) or saleable[:5]

        if andina:
            quote = self.env['sale.order'].create({
                'partner_id': andina.id,
                'user_id': andina.user_id.id,
                'origin': 'COT-2026-MULTI-01',
                'order_line': [
                    (0, 0, {
                        'product_id': prod.product_variant_id.id,
                        'product_uom_qty': random.randint(2, 6),
                        'price_unit': prod.list_price,
                    })
                    for prod in multi_products[:4]
                ],
            })

            sale = self.env['sale.order'].create({
                'partner_id': andina.id,
                'user_id': andina.user_id.id,
                'origin': 'PV-2026-MULTI-01',
                'order_line': [
                    (0, 0, {
                        'product_id': prod.product_variant_id.id,
                        'product_uom_qty': random.randint(1, 4),
                        'price_unit': prod.list_price,
                    })
                    for prod in multi_products[:5]
                ],
            })
            sale.action_confirm()
            invoice = sale._create_invoices()
            invoice.action_post()
            self._assign_invoice_name(invoice, 'INV/2026/00003')
            self._register_payment(invoice)

        if moto:
            quote = self.env['sale.order'].create({
                'partner_id': moto.id,
                'user_id': moto.user_id.id,
                'origin': 'COT-2026-MULTI-02',
                'order_line': [
                    (0, 0, {
                        'product_id': prod.product_variant_id.id,
                        'product_uom_qty': random.randint(1, 5),
                        'price_unit': prod.list_price,
                    })
                    for prod in multi_products[1:5]
                ],
            })

            sale = self.env['sale.order'].create({
                'partner_id': moto.id,
                'user_id': moto.user_id.id,
                'origin': 'PV-2026-MULTI-02',
                'order_line': [
                    (0, 0, {
                        'product_id': prod.product_variant_id.id,
                        'product_uom_qty': random.randint(2, 5),
                        'price_unit': prod.list_price,
                    })
                    for prod in multi_products[:4]
                ],
            })
            sale.action_confirm()
            invoice = sale._create_invoices()
            overdue_date = fields.Date.today() - timedelta(days=30)
            invoice.write({
                'invoice_date': overdue_date,
                'invoice_date_due': overdue_date,
            })
            invoice.action_post()
            self._assign_invoice_name(invoice, 'INV/2026/00004')

    @api.model
    def _create_anchor_cases(self, partners, products, orders):
        andina = partners.filtered(lambda p: p.name == 'Comercial Andina S.A.')[:1]
        moto = partners.filtered(lambda p: p.name == 'Moto Racing Cuenca')[:1]
        casco = products.filtered(lambda p: p.default_code == 'CAS-001')[:1]
        filtro = products.filtered(lambda p: p.default_code == 'FIL-M01')[:1]

        if andina and casco:
            self._create_anchor_invoice_paid(andina, casco, 1250.00, 'INV/2026/00001')
        if moto and filtro:
            self._create_anchor_invoice_overdue(moto, filtro, 840.00, 'INV/2026/00002')

    @api.model
    def _create_anchor_invoice_paid(self, partner, product, total, invoice_name):
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'user_id': partner.user_id.id,
            'origin': 'PV-2026-ANCLA-01',
            'order_line': [(0, 0, {
                'product_id': product.product_variant_id.id,
                'product_uom_qty': max(1, int(total / product.list_price)),
                'price_unit': product.list_price,
            })],
        })
        order.action_confirm()
        invoice = order._create_invoices()
        if len(invoice.invoice_line_ids) > 1:
            invoice.invoice_line_ids[1:].unlink()
        line = invoice.invoice_line_ids[:1]
        if line:
            # Sin impuestos: el total de la factura ancla debe ser exactamente el indicado.
            line.write({'quantity': 1, 'price_unit': total, 'tax_ids': [(5, 0, 0)]})
        invoice.action_post()
        self._assign_invoice_name(invoice, invoice_name)

        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': partner.id,
            'amount': total,
            'journal_id': self._get_bank_journal().id,
        })
        payment.action_post()
        (invoice + payment.move_id).line_ids.filtered(
            lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')
        ).reconcile()

    @api.model
    def _assign_invoice_name(self, invoice, invoice_name):
        if invoice.name == invoice_name:
            return
        if self.env['account.move'].search_count([
            ('name', '=', invoice_name),
            ('id', '!=', invoice.id),
        ]):
            return
        invoice.write({'name': invoice_name})

    @api.model
    def _create_anchor_invoice_overdue(self, partner, product, total, invoice_name):
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'user_id': partner.user_id.id,
            'origin': 'PV-2026-ANCLA-02',
            'order_line': [(0, 0, {
                'product_id': product.product_variant_id.id,
                'product_uom_qty': max(1, int(total / max(product.list_price, 1))),
                'price_unit': product.list_price,
            })],
        })
        order.action_confirm()
        invoice = order._create_invoices()
        overdue_date = fields.Date.today() - timedelta(days=45)
        invoice.write({
            'invoice_date': overdue_date,
            'invoice_date_due': overdue_date,
        })
        if len(invoice.invoice_line_ids) > 1:
            invoice.invoice_line_ids[1:].unlink()
        line = invoice.invoice_line_ids[:1]
        if line:
            # Sin impuestos: el total de la factura ancla debe ser exactamente el indicado.
            line.write({'quantity': 1, 'price_unit': total, 'tax_ids': [(5, 0, 0)]})
        invoice.action_post()
        self._assign_invoice_name(invoice, invoice_name)

    @api.model
    def _create_additional_invoices(self, partners, products):
        customers = partners.filtered(lambda p: p.customer_rank > 0 and p.ref != MARKER_REF)
        saleable = products.filtered('sale_ok')
        created = 0
        attempt = 0
        max_attempts = TARGET_INVOICES * 4

        while created < TARGET_INVOICES and attempt < max_attempts:
            attempt += 1
            partner = random.choice(customers)
            force_multi = created % 3 == 0
            order_lines = self._build_order_lines(saleable, force_multi=force_multi)
            if not order_lines:
                continue

            order = self.env['sale.order'].create({
                'partner_id': partner.id,
                'user_id': partner.user_id.id,
                'origin': f'PV-2026-FAC-{created + 1:04d}',
                'order_line': order_lines,
            })
            roll = random.random()
            if roll < 0.08:
                continue

            order.action_confirm()
            if roll < 0.12:
                continue

            invoice = order._create_invoices()
            if roll < 0.18:
                continue

            if roll < 0.42:
                due = fields.Date.today() - timedelta(days=random.randint(10, 75))
                invoice.write({'invoice_date_due': due})
            invoice.action_post()

            if roll < 0.72:
                self._register_payment(invoice)
            created += 1

    @api.model
    def _register_payment(self, invoice):
        if invoice.payment_state == 'paid':
            return
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': invoice.partner_id.id,
            'amount': invoice.amount_residual,
            'journal_id': self._get_bank_journal().id,
        })
        payment.action_post()
        lines = (invoice + payment.move_id).line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
        )
        if lines:
            lines.reconcile()

    @api.model
    def _get_bank_journal(self):
        journal = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not journal:
            raise UserError(_('No se encontró diario bancario.'))
        return journal
