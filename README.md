# Tufup Example - Sistema de Actualizaciones

Este proyecto implementa un sistema de actualizaciones automáticas usando [tufup](https://github.com/dennisvang/tufup) (basado en TUF - The Update Framework).

## Requisitos

- Python 3.10+
- Windows 10/11 (o adaptar para macOS/Linux)

## Instalación

```powershell
pip install -r requirements.txt -r requirements-dev.txt --upgrade
```

## Configuración inicial

### 1. Configurar URLs del servidor

Edita `src/myapp/settings.py` y cambia las URLs a tu servidor:

```python
METADATA_BASE_URL = 'http://servidor:puerto/metadata/'
TARGET_BASE_URL = 'http://servidor:puerto/targets/'
```

Para pruebas locales puedes usar:

```python
METADATA_BASE_URL = 'http://localhost:8000/metadata/'
TARGET_BASE_URL = 'http://localhost:8000/targets/'
```

### 2. Inicializar el repositorio

```powershell
python .\repo_init.py
```

Esto crea:

- Claves criptográficas en `temp_my_app/keystore/`
- Metadatos TUF en `temp_my_app/repository/metadata/`

### 3. Crear el bundle de la aplicación (windows)

```powershell
.\create_pyinstaller_bundle_win.bat
```

### 4. Agregar el bundle al repositorio

```powershell
python .\repo_add_bundle.py
```

### 5. Servir el repositorio (para pruebas locales)

```powershell
python -m http.server -d temp_my_app/repository
```

## Publicar una nueva versión

1. Incrementa `APP_VERSION` en `src/myapp/settings.py`
2. Ejecuta `.\create_pyinstaller_bundle_win.bat`
3. Ejecuta `python .\repo_add_bundle.py`
4. Sube los archivos de `temp_my_app/repository/` a tu servidor

## Instalación en cliente (simulación)

1. Extrae el archivo `temp_my_app/repository/targets/my_app-X.X.tar.gz` en `%LOCALAPPDATA%\Programs\my_app`
2. Ejecuta `main.exe` desde esa ubicación

## Configuración de expiración

Los metadatos TUF tienen una fecha de expiración configurada en `repo_settings.py`:

```python
EXPIRATION_DAYS = dict(root=730, targets=730, snapshot=730, timestamp=730)
```

Actualmente configurado a **730 días (2 años)**.

## Estructura del proyecto

```
tufup-example/
├── src/
│   ├── myapp/           # Código de la aplicación
│   │   ├── __init__.py  # Lógica de actualización
│   │   └── settings.py  # Configuración (URLs, versión, etc.)
│   ├── customdiff/      # HDiffPatch para parches binarios
│   └── main.py          # Punto de entrada
├── repo_init.py         # Inicializa el repositorio TUF
├── repo_add_bundle.py   # Agrega nuevas versiones
├── repo_settings.py     # Configuración del repositorio
├── main.spec            # Configuración de PyInstaller
└── temp_my_app/         # (generado) Repositorio local
    ├── keystore/        # Claves privadas
    └── repository/      # Metadatos y archivos para distribución
```
