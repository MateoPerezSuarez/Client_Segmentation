import pandas as pd

orders = pd.read_csv('data/olist/olist_orders_dataset.csv')
product_price = pd.read_csv('data/olist/olist_order_items_dataset.csv')[['order_id', 'product_id','price','freight_value']]
payments = pd.read_csv('data/olist/olist_order_payments_dataset.csv')[['order_id','payment_value']]


# Agrupar los datos de productos de cada compra
# Dejar los datos guardados de lista de productos para ver que pasa
product_price_grouped = (
    product_price.groupby("order_id", as_index=False)
      .agg(
          product_id=("product_id", list),
          precio_items=("price", "sum"),
          precio_total=("order_id", lambda x: 0)
      )
)

product_price_grouped["precio_total"] = (
    product_price.groupby("order_id")[["price", "freight_value"]]
      .sum()
      .sum(axis=1)
      .to_numpy()
)

# Unir los datos de los productos y el total pagado con el dataset de los orders

orders_final = (
    orders.merge(product_price_grouped, on="order_id"))

orders_final = orders_final[['order_id', 'customer_id', 'order_purchase_timestamp','product_id', 'precio_items', 'precio_total']]

orders_final.to_parquet('data/olist/datos_requeridos/olist_final.parquet', index=False)






