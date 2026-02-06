# TODO - Wallapop Scraper

## 🔴 CRÍTICO - Funcionalidad Esencial

### 1. Verificar y Solucionar Problemas de Ejecución
- [x] ~~Resolver problema de entorno Python (selenium no encontrado)~~
- [x] ~~Probar ejecución completa con una búsqueda de prueba~~
- [x] ~~Verificar que se generen correctamente los CSV y logs~~
- [x] ~~Documentar los pasos exactos de ejecución en README~~

### 2. Indetectabilidad - Protección Anti-Bot
- [ ] **Randomizar tiempos de espera**: Actualmente usa `time.sleep()` con valores fijos, muy detectable
  - Implementar delays aleatorios entre 2-5 segundos
  - Variar tiempos entre acciones (click, scroll, navegación)
- [ ] **User-Agent rotación**: Agregar rotación de user agents
- [ ] **Simular comportamiento humano**:
  - Scroll gradual en la página de resultados antes de extraer datos
  - Movimientos de mouse aleatorios
  - Pausas aleatorias al navegar entre productos
- [ ] **Headers adicionales**: Agregar headers realistas (Accept-Language, Accept-Encoding, etc.)
- [ ] **Verificar configuración de undetected-chromedriver**:
  - Revisar que esté usando la versión más reciente
  - Configurar opciones adicionales para evasión (disable-blink-features, etc.)

### 3. Gestión Robusta de Errores
- [ ] **Manejo de cookies**: El bloque try-except es muy genérico, puede fallar silenciosamente
  - Agregar reintentos si falla la aceptación de cookies
  - Verificar que las cookies se hayan aceptado correctamente
- [ ] **Búsqueda**: Si falla `perform_search`, el programa crashea - necesita manejo mejor
- [ ] **Elementos no encontrados**: Mejorar los mensajes de error cuando no se encuentran elementos
- [ ] **Timeout configurables**: Los WebDriverWait usan valores fijos (10, 20), hacerlos configurables
- [ ] **Reintentos**: Implementar sistema de reintentos para páginas que no cargan

### 4. Validación de Datos Extraídos
- [ ] **Verificar que se extraen datos**: Algunos items pueden tener estructura diferente
- [ ] **Validar URLs**: Asegurar que las URLs son válidas antes de visitarlas
- [ ] **Limpiar datos**: Eliminar espacios extras, caracteres especiales en precios
- [ ] **Detectar productos sin stock/eliminados**: Manejar cuando un producto ya no está disponible

## 🟡 IMPORTANTE - Estabilidad y Mejoras

### 5. Optimización de Esperas y Carga
- [ ] **Esperas inteligentes**: Reemplazar `time.sleep()` fijos por esperas explícitas (WebDriverWait)
- [ ] **Verificar carga completa**: Asegurar que la página de resultados cargó todos los items
- [ ] **Scroll para cargar más items**: Wallapop carga items dinámicamente, implementar scroll automático
- [ ] **Detección de fin de resultados**: Saber cuándo ya no hay más productos que cargar

### 6. Configuración Externalizada
- [ ] **Crear config.py o config.json**:
  - Timeouts (min/max delays, wait times)
  - Selectores CSS (fácil actualización si Wallapop cambia el DOM)
  - Opciones de headless/visible
  - Número máximo de items a scrapear
  - URL base de Wallapop
- [ ] **Variables de entorno**: Para configuraciones sensibles

### 7. Mejoras en Logging
- [ ] **Niveles de log apropiados**: Usar DEBUG para detalles técnicos, INFO para progreso
- [ ] **Logs más informativos**: Agregar contexto (timestamp, query, número de items)
- [ ] **Log de sesión completa**: Resumen al final (items extraídos, errores encontrados, tiempo total)
- [ ] **Consola + archivo**: Mostrar progreso en consola además del archivo log

### 8. Estructura de Código
- [ ] **Separar responsabilidades**: Crear módulos separados
  - `scraper.py`: Lógica de scraping
  - `parser.py`: Extracción y limpieza de datos
  - `config.py`: Configuración
  - `utils.py`: Funciones auxiliares (delays, logging, etc.)
- [ ] **Clases**: Convertir a OOP para mejor mantenibilidad
  - Clase `WallapopScraper` con métodos bien definidos

### 9. Casos Edge y Validaciones
- [ ] **Sin resultados**: Manejar búsquedas que no retornan productos
- [ ] **Caracteres especiales**: Sanitizar query antes de usar en nombres de archivos
- [ ] **Límite de páginas**: Evitar loops infinitos si hay muchos resultados
- [ ] **Conexión perdida**: Detectar y recuperarse de pérdida de conexión
- [ ] **Captcha detection**: Detectar si aparece un captcha y pausar/notificar

### 10. Datos Adicionales a Extraer
- [ ] **Imágenes**: URLs de las imágenes del producto
- [ ] **Fecha de publicación**: Cuándo se publicó el anuncio
- [ ] **Estado del producto**: Nuevo, como nuevo, buen estado, etc.
- [ ] **Vendedor**: Nombre/ID del vendedor (si está disponible)
- [ ] **Categoría**: Categoría del producto
- [ ] **Número de favoritos/vistas**: Si está disponible públicamente

## 🟢 FUTURO - Funcionalidades Avanzadas

### 11. Base de Datos (Próxima fase)
- [ ] **Diseñar esquema**: Tablas para productos, búsquedas, histórico de precios
- [ ] **SQLite o PostgreSQL**: Decidir motor de base de datos
- [ ] **ORM**: Considerar usar SQLAlchemy para facilitar el manejo
- [ ] **Migración de datos**: Script para importar CSVs existentes

### 12. Seguimiento de Precios (Requiere BBDD)
- [ ] **Tabla de histórico**: Registrar cambios de precio con timestamp
- [ ] **Comparación**: Detectar bajadas/subidas de precio
- [ ] **Alertas**: Notificar cuando un producto baja de precio

### 13. Sistema de Notificaciones (Requiere BBDD)
- [ ] **Email**: Enviar resumen de nuevos productos por email
- [ ] **Telegram/Discord**: Bot para notificaciones en tiempo real
- [ ] **Alertas de precio**: Notificar cuando precio baje del umbral deseado

### 14. Filtros Avanzados
- [ ] **Rango de precios**: Filtrar por precio mínimo/máximo
- [ ] **Ubicación**: Filtrar por ciudad o distancia
- [ ] **Estado**: Filtrar por estado del producto
- [ ] **Fecha**: Solo productos publicados en las últimas X horas/días
- [ ] **Palabras clave**: Incluir/excluir productos con ciertas palabras

### 15. Paginación y Volumen
- [ ] **Scraping de múltiples páginas**: Navegar por todas las páginas de resultados
- [ ] **Límite configurable**: Máximo de items/páginas a scrapear por búsqueda
- [ ] **Progreso visual**: Barra de progreso para scraping largo

### 16. Múltiples Búsquedas
- [ ] **Archivo de búsquedas**: Leer múltiples queries desde un archivo
- [ ] **Búsqueda programada**: Ejecutar búsquedas automáticamente cada X tiempo
- [ ] **Modo batch**: Procesar múltiples búsquedas en una sola ejecución

### 17. Interfaz de Usuario
- [ ] **CLI mejorada**: Argumentos de línea de comandos (argparse)
  - `python main.py --query "MacBook" --max-items 50 --headless`
- [ ] **GUI**: Interfaz gráfica simple (Tkinter/PyQt) para usuarios no técnicos
- [ ] **Dashboard web**: Flask/FastAPI para visualizar datos y controlar scraping

### 18. Exportación de Datos
- [ ] **JSON**: Exportar resultados en formato JSON
- [ ] **Excel**: Generar archivos .xlsx con formato
- [ ] **API REST**: Servir datos a través de API

### 19. Testing y Calidad
- [ ] **Tests unitarios**: Probar funciones individuales
- [ ] **Tests de integración**: Probar flujo completo (con mock de Wallapop)
- [ ] **Linting**: Configurar flake8/black para calidad de código
- [ ] **Type hints**: Agregar anotaciones de tipos

### 20. Optimización de Rendimiento
- [ ] **Scraping paralelo**: Múltiples búsquedas simultáneas
- [ ] **Cache**: Cachear resultados para evitar scraping repetido
- [ ] **Headless por defecto**: Más rápido en producción

## 📝 Notas Importantes

### Prioridad de Implementación (Orden Recomendado)
1. **Semana 1**: Crítico #1-4 (Hacer que funcione de forma confiable)
2. **Semana 2**: Importante #5-7 (Estabilidad e indetectabilidad mejorada)
3. **Semana 3**: Importante #8-10 (Código limpio y casos edge)
4. **Mes 2**: Futuro #11-13 (Base de datos y notificaciones)
5. **Mes 3+**: Futuro #14-20 (Features avanzadas)

### Consideraciones de Indetectabilidad
- **Nunca** hacer requests demasiado rápido (mínimo 2-3 segundos entre acciones)
- **Siempre** usar delays aleatorios, no valores fijos
- **Monitorear** si Wallapop actualiza sus medidas anti-bot
- **Respetar** robots.txt y términos de servicio

### Mantenimiento
- **Actualizar selectores CSS**: Wallapop puede cambiar su HTML en cualquier momento
- **Revisar undetected-chromedriver**: Mantener actualizada la librería
- **Logs**: Revisar logs regularmente para detectar problemas temprano
