MODELO_DATOS = {
    "customer_id": {
        "required": True,
        "dtype": "string",
        "description": "Identificador único del cliente"
    },
    "transaction_id": {
        "required": True,
        "dtype": "string",
        "description": "Identificador único de la transacción"
    },
    "transaction_date": {
        "required": True,
        "dtype": "datetime64[ns]",
        "description": "Fecha de la transacción"
    },
    "transaction_amount": {
        "required": True,
        "dtype": "float64",
        "description": "Importe de la transacción"
    },
}

# Ejemplos de mapeos para diferentes clientes
# Estos se pueden definir aquí o en archivos de configuración separados

MAPEO_CLIENTE_ESTANDAR = {
    "customer_id": "customer_id",
    "transaction_id": "transaction_id",
    "transaction_date": "transaction_date",
    "transaction_amount": "transaction_amount",
}

MAPEO_CLIENTE_A = {
    "customer_id": "id_cliente",
    "transaction_id": "num_transaccion",
    "transaction_date": "fecha",
    "transaction_amount": "importe",
}

MAPEO_CLIENTE_B = {
    "customer_id": "ClienteID",
    "transaction_id": "PedidoNum",
    "transaction_date": "FechaCompra",
    "transaction_amount": "Total_EUR",
}