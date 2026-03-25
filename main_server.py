import threading
import logging
import uvicorn

from src.database import init_db
from src.scheduler import run_scheduler
from src.api import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def main():
    # Inicializar la base de datos
    init_db()

    # Lanzar scheduler en un thread daemon
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logging.info("Scheduler iniciado en background.")

    # Lanzar uvicorn en el thread principal
    logging.info("Iniciando API en http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
