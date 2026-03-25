import undetected_chromedriver as uc
import os
import shutil

def init_driver(headless=False, pos="max"):
    """
    Inicializa el driver de Chrome indetectable.
    """
    options = uc.ChromeOptions()
    options.add_argument("--password-store=basic")
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        },
    )

    if headless:
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--no-first-run")
        options.add_argument("--no-zygote")

    try:
        driver = uc.Chrome(
            options=options,
            headless=headless,
            log_level=3,
            use_subprocess=True
        )
    except Exception as e:
        print(f"Error inicializando driver: {e}. Intentando limpiar caché...")
        cache_path = os.path.join(os.getenv('APPDATA') or os.path.expanduser('~'), 'undetected_chromedriver')
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path, ignore_errors=True)
            
        # Reintentar con nuevas opciones
        options = uc.ChromeOptions()
        options.add_argument("--password-store=basic")
        driver = uc.Chrome(
            options=options,
            headless=headless,
            log_level=3,
            use_subprocess=True
        )
    
    if not headless:
        driver.maximize_window()
        if pos != "max":
            try:
                ancho, alto = driver.get_window_size().values()
                if pos == "izquierda":
                    driver.set_window_rect(x=0, y=0, width=ancho//2, height=alto)
                elif pos == "derecha":
                    driver.set_window_rect(x=ancho//2, y=0, width=ancho//2, height=alto)
            except Exception:
                pass # Ignorar errores de redimensionado si fallan
                
    return driver
