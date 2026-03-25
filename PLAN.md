# Plan: Wallapop Scraper como servicio continuo en CasaOS

## Objetivo
Convertir el scraper actual (CLI one-shot) en un servicio que corra 24/7 en el servidor CasaOS (192.168.1.100), scrapeando precios continuamente y exponiendo una API para consultar los mejores precios.

---

## Fase 1: Base de datos SQLite

Reemplazar la salida CSV por una base de datos persistente.

- [ ] Crear módulo `src/database.py` con SQLAlchemy/sqlite3
- [ ] Tabla `items`:
  - `id` (PK autoincrement)
  - `wallapop_url` (unique)
  - `title`
  - `price` (float, parseado del texto)
  - `description`
  - `location`
  - `query` (la búsqueda que lo encontró)
  - `first_seen` (datetime)
  - `last_seen` (datetime)
  - `price_history` (JSON string — lista de `{price, date}`)
- [ ] Lógica de upsert: si el item (por URL) ya existe, actualizar `last_seen` y añadir al historial si el precio cambió
- [ ] Adaptar `WallapopScraper.run()` para guardar en DB en vez de CSV

## Fase 2: Scheduler continuo

Ejecutar scrapes periódicamente para una lista configurable de búsquedas.

- [ ] Crear `searches.json` con la lista de búsquedas:
  ```json
  {
    "searches": [
      {"query": "MacBook M2", "interval_minutes": 60},
      {"query": "iPhone 15", "interval_minutes": 120}
    ]
  }
  ```
- [ ] Crear módulo `src/scheduler.py` que:
  - Lee `searches.json`
  - Ejecuta cada búsqueda según su intervalo
  - Gestiona el ciclo de vida del driver (abrir, scrapear N búsquedas, cerrar)
  - Logging de cada ciclo
- [ ] Adaptar `init_driver()` para modo headless obligatorio en servidor (sin display)
- [ ] Manejo de errores robusto: si un scrape falla, loguear y continuar con el siguiente

## Fase 3: API REST con FastAPI

Exponer los datos para consultas.

- [ ] `pip install fastapi uvicorn`
- [ ] Crear `src/api.py` con endpoints:
  - `GET /api/items` — listar items con filtros:
    - `?query=macbook` (búsqueda en título)
    - `?sort=price_asc|price_desc|recent`
    - `?max_price=500`
    - `?limit=50&offset=0`
  - `GET /api/items/{id}` — detalle de un item + historial de precios
  - `GET /api/searches` — listar búsquedas activas
  - `POST /api/searches` — añadir nueva búsqueda
  - `DELETE /api/searches/{query}` — eliminar búsqueda
  - `GET /api/stats` — resumen (total items, última ejecución, etc.)
- [ ] Crear `main_server.py` como entry point que lanza API + scheduler en paralelo

## Fase 4: Docker para CasaOS

Empaquetar todo para despliegue sencillo.

- [ ] `Dockerfile`:
  - Base: `python:3.11-slim`
  - Instalar Chrome + chromedriver (headless)
  - Copiar código + instalar dependencias
  - Exponer puerto 8000
  - CMD: `python main_server.py`
- [ ] `docker-compose.yml`:
  - Servicio `wallapop-scraper`
  - Volúmenes: `./data:/app/data` (SQLite DB), `./logs:/app/logs`
  - Puerto: `8000:8000`
  - Restart: `always`
- [ ] Actualizar `requirements.txt` con nuevas dependencias

## Fase 5 (opcional): Dashboard web

Frontend mínimo para ver resultados sin usar curl.

- [ ] Página HTML servida por FastAPI (Jinja2 o static)
- [ ] Vista de items con tabla ordenable
- [ ] Filtros por búsqueda, rango de precio
- [ ] Gráfica de historial de precio por item

---

## Orden de implementación

```
Fase 1 (DB) → Fase 2 (Scheduler) → Fase 3 (API) → Fase 4 (Docker) → Fase 5 (Dashboard)
```

Cada fase es funcional por sí misma. Podemos probar localmente hasta Fase 3 y luego dockerizar.

## Decisiones pendientes

- **Frecuencia de scraping**: ¿Cada cuánto? (propuesta: 60 min por defecto)
- **Búsquedas iniciales**: ¿Qué productos monitorear?
- **Dashboard**: ¿Necesario ahora o solo API?
- **Notificaciones**: ¿Alertas cuando un precio baje? (Telegram bot, email, etc.)
