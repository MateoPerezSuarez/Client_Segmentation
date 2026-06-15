# Plan de despliegue en Google Cloud — Client Segmentation

> Documento de plan. No incluye ejecución; sirve para alinear al equipo antes de
> empezar. Fecha: 2026-06-12.

## 1. Objetivo

Llevar la herramienta de segmentación automática de clientes a un despliegue en
Google Cloud que:

- escale a varios usuarios del equipo sin romperse,
- sea seguro (sin credenciales expuestas),
- y abra la puerta a una capa **agéntica vía MCP** para flujos de
  interpretación y acción, no solo de cálculo.

**Decisiones tomadas:**

- El **frontend** se ejecuta **en local** (React + Vite), apuntando al backend
  (local en desarrollo, o el Cloud Run ya desplegado). No entra en el alcance del
  despliegue cloud en esta fase.
- El backend objetivo es **Cloud Run** (ya está desplegado).

## 2. Punto de partida (lo que ya existe)

No partimos de cero; hay un MVP ya en cloud.

| Pieza | Estado actual | Ubicación |
|-------|---------------|-----------|
| Backend API | FastAPI dockerizado (multi-stage, non-root, puerto 8080), desplegado en Cloud Run | `product/backend/`, `Dockerfile`, `deploy.sh` |
| Cloud Run | Proyecto `segmentacion-491208`, región `europe-west1`, servicio `client-segmentation-api`, `0–5` instancias, `--allow-unauthenticated` | `deploy.sh` |
| Frontend | React + Vite, ejecutándose en local | `product/frontend/` |
| Fuente de datos | BigQuery integrado como alternativa a CSV/Excel | `services/bigquery_connector.py` |
| Motores | RFM quintiles, RFM k-means, ABC, LRFMS — bien separados en la capa de servicios | `services/segmentation/` |

El código está **limpiamente troceado en `services/`**, lo cual es clave: tanto
el REST API como un futuro servidor MCP son simples fachadas sobre esa misma
capa.

## 3. Problemas críticos a resolver (bloqueantes)

Estos no son mejoras opcionales: son cosas rotas o peligrosas en cuanto haya más
de un usuario.

### 3.1. Estado de sesión en memoria  — *bloqueante de escalado*

`core/session_store.py` guarda los DataFrames en un diccionario en memoria del
proceso (el propio comentario dice *"Swap _store for Redis in production"*).

En Cloud Run con `min-instances 0`, `max 5` y sin afinidad de sesión:

- el `/upload` cae en la instancia A, pero el `/clean` o `/segment` puede caer en
  la instancia B → error *"session not found"*,
- un cold start borra todo el estado.

Es el **bloqueante número uno** para que la herramienta funcione con varios
usuarios.

### 3.2. Service accounts commiteadas en git — *bloqueante de seguridad*

Hay dos claves de service account versionadas en el repo:

- `segmentacion-491208-22f600ce747c.json` (raíz)
- `cl/elite-firefly-480109-c9-fc816fd492b2.json`

Cualquiera con acceso al repositorio tiene las llaves del proyecto GCP. Acción:
**revocar en IAM, rotar, eliminar del histórico de git, y no volver a versionar
claves jamás.**

### 3.3. Credenciales de BigQuery viajando por el navegador

El endpoint `/upload/bigquery` (`routers/upload.py`) recibe el JSON completo de la
service account desde el frontend (`req.credentials_json`). Eso implica pasar una
llave de GCP por el cliente.

Solución: usar la **identidad propia del servicio Cloud Run** (Workload Identity /
Application Default Credentials). El backend ya corre dentro de GCP, no necesita
que nadie le pase llaves.

## 4. Arquitectura objetivo

Dos rutas de entrada que convergen en la misma capa de servicios:

```
Equipo (navegador, local)          Agente Claude (Desktop / Code / SDK)
        │ HTTPS REST                        │ MCP (HTTP)
        ▼                                    ▼
 Cloud Run · REST API (FastAPI)     Cloud Run · servidor MCP (FastMCP)
        └──────────────┬─────────────────────┘
                       ▼
        Capa de servicios compartida
        (parsing · limpieza · RFM · ABC · LRFMS)
                       ▼
   ┌───────────────┬───────────────┬──────────────────┐
   ▼               ▼               ▼                  
 Cloud Storage   BigQuery     Secret Manager
 (sesiones/      (fuente      (credenciales / SA)
  resultados)     de datos)

Transversal: CI/CD (Artifact Registry + Cloud Build) · Auth (IAP / IAM)
```

## 5. Plan por fases

### Fase 0 — Seguridad y orden

Estado de ejecución:

- [x] **Credenciales fuera del navegador.** El conector de BigQuery usa ahora
  ADC / Workload Identity (la identidad del propio servicio); se eliminó el
  envío de la clave JSON desde el frontend (backend + UI + traducciones).
- [x] **Secretos fuera del repo.** Desversionados y borrados
  `segmentacion-491208-22f600ce747c.json` y
  `cl/elite-firefly-480109-c9-fc816fd492b2.json`; `.gitignore` endurecido para
  bloquear claves, `.env`, `.pem`, `__pycache__`, `.DS_Store`, etc.
- [x] **Artifact Registry.** `deploy.sh` migrado de `gcr.io` (deprecado) a
  Artifact Registry, con SA de runtime dedicada y `BIGQUERY_PROJECT`.
- [x] **Script de infra** `infra/setup_security.sh`: crea el repo de Artifact
  Registry, la **SA de mínimo privilegio** (`bigquery.dataViewer` +
  `bigquery.jobUser`, sin claves descargables) y los bindings.

Pendiente de confirmación (operaciones irreversibles / hacia fuera):

- [ ] Ejecutar `infra/setup_security.sh` (crea recursos IAM en GCP).
- [ ] Re-desplegar con el nuevo `deploy.sh` para que Cloud Run deje de usar la
  SA de Compute por defecto.
- [ ] Reescritura del histórico de git + `force-push` para borrar las claves de
  los commits antiguos. La clave de `segmentacion` **ya fue deshabilitada
  automáticamente por Google** al detectarla en GitHub, así que esto es higiene,
  no urgencia.
- [ ] **Rotar la clave del proyecto `elite-firefly-480109-c9`** (es de otro
  proyecto distinto; hay que hacerlo desde allí).

### Fase 1 — Estado compartido (desbloquea el escalado)

Recomendado: **GCS como almacén de sesión**.

- Guardar los DataFrames intermedios como Parquet en un bucket, con clave
  `session_id` y *lifecycle rule* de borrado a 24h.
- Cero infraestructura *always-on*; encaja con serverless. Solo cambia
  `session_store.py`.

Alternativa: **Memorystore (Redis)** — más rápido y con TTL nativo, pero es un
recurso encendido 24/7 (~25–40 €/mes el más pequeño). Solo si la latencia importa
mucho.

Parche inmediato barato: activar `--session-affinity` en Cloud Run (mitiga, no
resuelve los cold starts).

### Fase 2 — Frontend

Fuera del alcance: se ejecuta **en local**, apuntando al backend vía
`VITE_API_BASE_URL`. Si en el futuro se quisiera desplegar en GCP, la opción más
simple sería **Firebase Hosting** (CDN incluido) frente a Cloud Storage + Load
Balancer. Sin urgencia técnica.

### Fase 3 — Autenticación de equipo

Hoy el backend es `--allow-unauthenticated` (abierto a internet). Para una
herramienta interna: **Identity-Aware Proxy (IAP)** delante de Cloud Run,
restringido al dominio de Google Workspace. Sin gestión de contraseñas.

### Fase 4 — Jobs largos (solo si crecen los datos)

Para datasets grandes, la segmentación síncrona puede chocar con el timeout de
Cloud Run. Camino de escalado: **Cloud Run Jobs** o cola con **Cloud
Tasks/Pub-Sub** → resultado a GCS → el frontend hace polling. No es necesario
ahora.

### Fase 5 — CI/CD

Sustituir el `deploy.sh` manual por un **trigger de Cloud Build** sobre `main`:
build → push a Artifact Registry → deploy a Cloud Run. Reproducible y sin
depender de una máquina concreta.

## 6. Capa MCP / agéntica

**Valoración:** MCP encaja bien, pero como capa **nueva en paralelo**, no como
sustituto del REST API ni del wizard.

Como `services/` ya está bien troceado, un servidor MCP es **otra fachada sobre la
misma capa de servicios** — el mismo patrón que el REST API. Se reutiliza todo.

**Montaje propuesto:** servidor MCP en Python (FastMCP) en su propio Cloud Run con
transporte HTTP/SSE, exponiendo herramientas como:

- `cargar_datos_bigquery(tabla)` / `cargar_csv(...)`
- `segmentar(metodo, parametros)`
- `describir_segmento(segmento)` → narrativa en lenguaje natural
- `recomendar_acciones(segmento)` → p.ej. "VIP en riesgo de fuga → campaña X"

**Qué desbloquea:**

- Pedirle a Claude *"segmenta la tabla de ventas Q2 por LRFMS y dime qué hacer con
  los clientes que están bajando"* y que el agente orqueste el pipeline.
- Informes narrativos automáticos por segmento (hoy el output es un CSV).
- Re-segmentaciones programadas/agénticas (cron → MCP → informe a Slack/email).

**Lo honesto:** para el usuario que solo sube un CSV y baja el resultado, el
wizard es más rápido y el MCP no aporta. El valor del MCP está en los flujos de
**interpretación y acción**, no de cálculo puro. Por eso van los dos en paralelo.

## 7. Orden recomendado de ejecución

1. **Fase 0** (seguridad) — urgente, independientemente de todo lo demás.
2. **Fase 1** (estado GCS) — bloqueante técnico real del escalado.
3. **Fase 3** (IAP) — barato y cierra el acceso público.
4. **Prototipo MCP** — validar la parte agéntica sobre la capa de servicios.
5. **Fase 5** (CI/CD) y **Fase 4** (jobs) — cuando el resto esté estable.

## 8. Persistencia del output (export a BigQuery / GCS)

El resultado de la segmentación (una tabla por cliente) puede guardarse
directamente en Google Cloud, sin pasar por la descarga manual del CSV.

**Decisión de diseño:** el resultado se materializa como **tabla en BigQuery**
(no como vista: la segmentación es un cómputo en Python, no SQL) y, en paralelo,
como **artefacto Parquet en GCS**. La vista solo se usa como puntero `_latest`.

- **Destino parametrizable.** El endpoint acepta destinos totalmente cualificados
  (`project.dataset.table` y `gs://bucket/prefix`), por lo que sirve igual para
  escribir en **el proyecto propio del cliente** (su BigQuery / sus buckets) que
  en **nuestro proyecto** para luego pasarle los resultados.
- **Historial (append).** Cada ejecución se añade particionada por
  `run_timestamp`, con columnas de metadatos `run_id`, `run_timestamp`, `method`
  y `params` (JSON). Permite comparar segmentaciones en el tiempo.
- **Vista `<tabla>_latest`** que apunta siempre al run más reciente: nombre
  estable para dashboards y consumidores.

**Implementado:**

- `services/exporter.py` — `export_to_bigquery()` (append + partición + vista
  `_latest`) y `export_to_gcs()` (Parquet).
- `POST /segment/export` — body `{ session_id, token, bq_table?, gcs_uri? }`.
- `requirements.txt` — añadidos `google-cloud-storage` y `pyarrow`.
- `infra/setup_security.sh` — la SA de runtime recibe `bigquery.dataEditor` y
  `storage.objectAdmin` en nuestro proyecto, y se documenta el grant
  cross-project (lo concede el cliente sobre su dataset/bucket).
- **Frontend:** botón "Guardar en Google Cloud" en el Step 6, con destino
  introducido a mano (tabla BQ y/o ruta `gs://…`) y feedback del resultado.

**Pendiente:** que se ejecute `setup_security.sh` (permisos de escritura) y, para
proyectos de cliente, que el cliente conceda a nuestra SA los roles indicados.

## 9. Notas de coste (orden de magnitud)

- Cloud Run con `min-instances 0`: prácticamente gratis en reposo; se paga por uso.
- GCS para sesiones: céntimos/mes con lifecycle de 24h.
- Memorystore (si se eligiera): ~25–40 €/mes el más pequeño (always-on).
- BigQuery: por consulta/almacenamiento; depende del volumen del dataset.
- IAP / Artifact Registry / Cloud Build: coste marginal para uso interno.
