import undetected_chromedriver as uc

def iniciar_uc(headless=False, pos = "max"):
    
    options = uc.ChromeOptions()
    options.add_argument("--password-store=basic")
    options.add_experimental_option(
        "prefs", 
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        },
    )
    
    driver = uc.Chrome(
        options=options, 
        headless=headless,
        log_level=3,
    )
    
    if not headless:
        driver.maximize_window()
        if pos != "max":
            ancho, alto = driver.get_window_size().values()
            if pos == "izquierda":
                driver.set_window_rect(x=0, y=0, width=ancho//2, height=alto)
            if pos == "derecha":
                driver.set_window_rect(x=ancho//2, y=0, width=ancho//2, height=alto)
    return driver
                

    