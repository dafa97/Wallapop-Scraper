# TODO - Wallapop Scraper

## ✅ Completado
- [x] **Configuración del entorno**: Solución de problemas con selenium y paths.
- [x] **Estructura del proyecto**: Refactorización a arquitectura modular (`src/scraper.py`, `src/driver.py`, etc.).
- [x] **Salida de datos**: Generación correcta de CSVs con timestamp en carpeta `output/`.
- [x] **Logging**: Sistema de logs configurado y guardando en carpeta `logs/`.
- [x] **Configuración centralizada**: Archivo `src/config.py` creado con constantes y selectores.
- [x] **Ejecución básica**: El scraper busca, lista resultados y entra al detalle de cada producto.
- [x] **CLI Arguments**: Permitir configurar `max_items` o modo `headless` desde argumentos de línea de comando.
- [x] **Page Object Model (POM)**: Refactorización completa a POM con herencia (`BasePage` → `HomePage`, `SearchResultsPage`, `ItemDetailPage`). Selectores movidos de `Config.SELECTORS` a cada Page Object. `scraper.py` ahora solo orquesta.
- [x] **Eliminar `time.sleep` → Esperas explícitas**: Todos los `sleep` reemplazados por `WebDriverWait` + `expected_conditions`. Único `sleep` restante es `anti_detection_delay()` con `random.uniform(2.5, 5.0)`.
- [x] **Tiempos de espera aleatorios**: Implementado `anti_detection_delay()` con `random.uniform(2.5, 5.0)` en `scraper.py`.
- [x] **Fix cookies Shadow DOM**: El banner de consentmanager.net se renderiza en Shadow DOM. Solucionado con `execute_script()` para acceder al shadow root de `#cmpwrapper`.

## 🚀 Prioridad Alta

### 1. Scraping paralelo de detalles (requests + ThreadPoolExecutor)
Las páginas de detalle devuelven título, precio y ubicación via HTTP plano (sin JS). La descripción completa requiere JS, pero `og:description` ofrece un resumen.
- [ ] Implementar fetcher con `requests` que extraiga datos de detalle sin Selenium.
- [ ] Paralelizar con `ThreadPoolExecutor` (3-5 workers).
- [ ] Copiar cookies/headers del navegador para las requests HTTP.
- [ ] Fallback a Selenium si la request falla o se necesita descripción completa.

### 2. Navegación humana
- [ ] **Scroll suave y aleatorio** antes de hacer click.

### 3. Extracción de Datos (Mejoras)
- [ ] **Paginación**: Implementar click en "Ver más productos" para scrapear más allá de los items visibles inicialmente.
- [ ] **Limpieza de datos**: Parsear precio a float (quitar símbolo € y espacios).
- [ ] **Imágenes**: Extraer URLs de las imágenes del producto.

## 🛠️ Mantenimiento y Robustez

### 4. Gestión de Errores
- [ ] **Reintentos automáticos**: Usar `tenacity` o decorador personalizado para reintentar acciones fallidas (ej. carga de página lenta, `StaleElementReferenceException`).

### 5. Calidad del Código
- [ ] **Type hints**: Añadir type hints a todas las funciones en `src/`.

## 💡 Ideas Futuras
- [ ] **Modo Headless Real**: Configurar ChromeDriver para headless sin ser detectado.
- [ ] **Notificaciones**: Avisar por email o Telegram cuando termina un scrape o encuentra palabras clave.
- [ ] **Base de Datos**: Guardar en SQLite en lugar de solo CSV para evitar duplicados entre ejecuciones.
