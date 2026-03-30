# Plan: Wallapop Scraper como servicio continuo en CasaOS

## Objetivo
Convertir el scraper actual (CLI one-shot) en un servicio que corra 24/7 en el servidor CasaOS (192.168.1.100), scrapeando precios continuamente y exponiendo una API para consultar los mejores precios.

---

## Fase 1: Base de datos SQLite ✅ COMPLETA

- [x] Crear módulo `src/database.py` con sqlite3
- [x] Tabla `items` con todos los campos planificados (id, wallapop_url, title, price, description, location, query, first_seen, last_seen, price_history)
- [x] Lógica de upsert: actualiza `last_seen` y añade al historial si el precio cambió
- [x] `WallapopScraper.run()` guarda en DB + CSV de backup

## Fase 2: Scheduler continuo ✅ COMPLETA

- [x] `searches.json` con búsquedas configuradas (Behringer XR18, Korg Nano, Teenage engineering — intervalo 30 min)
- [x] `src/scheduler.py` con clase `Scheduler` que lee `searches.json`, ejecuta por intervalo, recarga config cada 5 min
- [x] Driver en modo headless (`WallapopScraper(headless=True)`)
- [x] Manejo de errores: loguea y continúa con la siguiente búsqueda

## Fase 3: API REST con FastAPI ✅ COMPLETA

- [x] `GET /api/items` — filtros por query, sort, max_price, paginación
- [x] `GET /api/items/{id}` — detalle + historial de precios
- [x] `GET /api/searches` — listar búsquedas activas
- [x] `POST /api/searches` — añadir nueva búsqueda
- [x] `DELETE /api/searches/{query}` — eliminar búsqueda
- [x] `GET /api/stats` — resumen (total items, última ejecución, queries)
- [x] `GET /api/opportunities` — items por debajo del precio promedio de su query (con `discount_pct`)
- [x] `POST /api/scrape` — forzar scrape inmediato en background
- [x] `GET /api/scrape/status` — ver scrapes en curso
- [x] `main_server.py` como entry point que lanza API + scheduler en paralelo

## Fase 4: Docker para CasaOS ✅ COMPLETA

- [x] `Dockerfile` con Chrome headless
- [x] `docker-compose.yml`: volúmenes `./data`, `./logs`, `./searches.json`; puerto `8085:8000`; restart always
- [x] `requirements.txt` actualizado con fastapi, uvicorn, etc.

## Fase 5: Dashboard web ✅ COMPLETA

- [x] `static/index.html` servido por FastAPI
- [x] Vista de items con tabla
- [x] Pestaña de oportunidades (items con descuento respecto al promedio)

---

## Pendiente / Ideas futuras

- [ ] **Notificaciones**: alertas cuando un precio baje por debajo de un umbral (Telegram bot, etc.)
- [ ] **Historial de precios visual**: gráfica de precio por item en el dashboard
- [ ] **Filtros avanzados en UI**: rango de precio, ordenación en el frontend
- [ ] **Tests**: ninguno configurado aún
- [ ] **Autenticación**: la API es pública dentro de la red local; considerar si hace falta protegerla

## Decisiones tomadas

- **Frecuencia**: 30 min por búsqueda (configurable en `searches.json`)
- **Búsquedas activas**: Behringer XR18, Korg Nano, Teenage engineering (equipo de música/electrónica)
- **Puerto en CasaOS**: 8085 (evita conflictos con otros servicios)
- **Dashboard**: implementado con pestaña de oportunidades
