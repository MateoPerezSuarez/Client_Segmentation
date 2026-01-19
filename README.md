# Client_Segmentation

Vamos a seguir un formato experimental de métricas LRFMS, de las cuales cada una significa:

L(Longitud/Duracion) = Tiempo entre primera y última compra del cliente en el tiempo que se defina
        -> Indica lealtad, puede ayudarnos a diferencia entre un cliente nuevo y uno que mantiene relación a largo plazo.

R(Recencia) = Tiempo promedio entre el final del intervalo analizado y las últimas "p" transacciones.
        -> Respecto al valor normal de recencia, así eliminamos de cierta manera la aleatoriedad que podría haber al coger solo la última compra.

F(Frecuencia) = Numero total de transacciones realizadas por el cliente durante el intervalo que estemos analizando

M(Monetario) = Valor total de las transacciones en el intervalo analizado

S(Satisfacción) = Valor que se extrae de ponderar 3 factores: satisfacción con la calidad del producto, puntualidad de entrega y servicio de postventa
        -> Preguntar por esto porque en el estudio estos 3 factores son de una plataforma de colaboración de la que obtienen feedback del usuario sobre su experiencia


# Modelo de datos

Que columnas o datos puedo necesitar para realizar esta segmentación?

1- customer_id (Necesito para indentificar a cada cliente, y que es la piedra angular de esta segmentación)
2- order_id (Identificar los pedidos, en algunos casos he visto que en pedidos con muchos productos se repite el id del pedido, hay que tenerlo en cuenta)
3- order_date (Para calcular los intervalos de tiempo)
4- transaction_total_price (calcular el valor M, seguramente tenga que extraer del valor de cada producto del pedido y sumarlos)


