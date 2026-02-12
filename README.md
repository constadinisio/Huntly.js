# Huntly — Workana Job Scraper & Assistant

Un scraper y pipeline para detectar ofertas en Workana, generar propuestas y enviar notificaciones (Telegram / Email). El repositorio está organizado en paquetes para facilitar extensión y despliegue.

Resumen rápido
- Scrapea ofertas desde Workana.
- Persiste resultados en `data/` (CSV, JSON y SQLite).
- Integra generación de propuestas (AI) y envío automatizado.
- Notificaciones por Telegram y (opcional) Email.

Estructura principal del repo
- `huntly/`: paquete principal con submódulos:
  - `huntly/core` — almacenamiento, notificaciones y utilidades.
  - `huntly/workana` — scraper, sender (playwright) y bootstrap de sesión.
  - `huntly/integrations` — integraciones (Telegram bot).
  - `huntly/pipeline` — pipeline de propuestas y procesamiento.
  - `huntly/ai` — generación de propuestas (OpenAI u otra API).
- `config/`: archivos de configuración y ejemplo de entorno.
- `data/`: datos generados y persistencia (`workana_jobs.csv`, `workana_jobs.json`, `jobs.db`).

Archivos importantes
- [config/.env.example](config/.env.example)
- [main.py](main.py)
- [data/workana_jobs.csv](data/workana_jobs.csv)
- [data/workana_jobs.json](data/workana_jobs.json)
- [data/jobs.db](data/jobs.db)

Requisitos recomendados
- Python 3.11 o 3.12 (probado). Algunas dependencias como Playwright pueden requerir herramientas de sistema.
- Instala dependencias desde `requirements.txt`.

Instalación (manual)
```powershell
python -m venv .venv
.venv\Scripts\activate    # Windows (PowerShell/CMD)
pip install -r requirements.txt
```

Configuración inicial
- Copia el ejemplo de entorno y edítalo:
```powershell
copy config\.env.example config\.env   # Windows
```
- Valores importantes (en `config/.env`):
  - `WORKANA_URL`: URL de búsqueda en Workana.
  - `WORKANA_STATE_FILE`: archivo para Playwright storage state (por defecto `config/workana_state.json`).
  - `CSV_FILE` / `JSON_FILE`: si solo das un nombre se guardará en `data/`.
  - `TG_TOKEN`, `TG_CHAT`: para notificaciones por Telegram.
  - `OPENAI_API_KEY` (opcional): para generación automática de propuestas.

Inicio por primera vez
1. Guardar sesión de Playwright (solo si usas envío automático):

```powershell
python -m huntly.workana.bootstrap
# Sigue las instrucciones en la ventana del navegador para iniciar sesión en Workana
```

El bootstrap guardará `WORKANA_STATE_FILE` (por defecto `config/workana_state.json`).

2. Ejecutar la aplicación principal (bot + scraper):

```powershell
python main.py
```

`main.py` arranca el bot de Telegram en un hilo y ejecuta el scraper/pipeline en primer plano.

Modo desarrollo y pruebas
- Ejecutar solo el scraper:
```bash
python -m huntly.workana.scraper
```
- Ejecutar solo el bot (útil para desarrollo):
```bash
python -m huntly.integrations.telegram_bot
```

Persistencia y archivos generados
- Todos los archivos generados por defecto se almacenan en la carpeta `data/`:
  - `data/workana_jobs.csv` — CSV principal.
  - `data/workana_jobs.json` — respaldo JSON.
  - `data/jobs.db` — SQLite para estados y metadatos.

Si prefieres otra ruta, configura las variables `CSV_FILE`, `JSON_FILE` o `DB_FILE` en `config/.env`.

Instalador unificado (no interactivo opcional)
-----------------------------------------
Existe un script PowerShell que automatiza todo: `scripts/setup_and_run.ps1`.

Ejemplos:

- Ejecutar dentro del repo (interactivo):
```powershell
.\scripts\setup_and_run.ps1
```

- Ejecutar desde cualquier carpeta, clonar y correr sin interacción (proporcionando credenciales):
```powershell
.\scripts\setup_and_run.ps1 -RepoUrl 'https://github.com/constadinisio/Huntly.js.git' -InstallDir "$env:USERPROFILE\Huntly.js" -Force -NonInteractive -TGToken '<TU_TOKEN>' -TGChat '<TU_CHAT_ID>' -OpenAIKey '<TU_OPENAI_KEY>'
```

Con `-NonInteractive` el script no pedirá confirmaciones y ejecutará bootstrap y `main.py`. Si se pasan `-TGToken` y `-TGChat` estos valores se guardan en `config/.env` automáticamente.

Crear un Bot de Telegram (paso a paso)
-----------------------------------
1. Abre Telegram y busca `@BotFather`.
2. Envíale `/newbot` y sigue las instrucciones: elige un nombre y un username (debe terminar en "bot").
3. `@BotFather` te devolverá el `HTTP API token` (algo como `123456:ABC-DEF...`). Copia ese valor.
4. Para obtener tu `TG_CHAT` ID:
   - Opción A: envía un mensaje privado al bot y visita `https://api.telegram.org/bot<TOKEN>/getUpdates` (reemplaza `<TOKEN>`). Busca `chat`->`id` en la respuesta.
   - Opción B: añade el bot a un grupo y usa el mismo endpoint para leer el `chat.id` del grupo.
5. Coloca `TG_TOKEN` y `TG_CHAT` en `config/.env` o pásalos al script `setup_and_run.ps1` con `-TGToken` y `-TGChat`.

Con esto el bot podrá enviar notificaciones al chat/usuario configurado.

Notas operativas
- `config/.env` se carga desde `huntly/__init__.py`; no subas credenciales al control de versiones.
- Evitamos ejecutar efectos secundarios en import time; los scripts tienen `if __name__ == '__main__'` o se ejecutan con `-m`.
- Si mueves o renuevas la sesión de Playwright, actualiza `WORKANA_STATE_FILE`.

Depuración
- Logs se imprimen en consola; para más detalle ajusta el nivel de logging en `config/.env` o dentro de `huntly/core`.

Contribuir
- Si quieres colaborar: abre un issue con la propuesta o un PR siguiendo el estilo del repositorio.

Licencia
- Revisa el archivo `LICENSE` en la raíz.

Contacto
- Mantenedor: @constadinisio
# Workana Job Scraper 🚀

Un scraper robusto y automatizado para extraer ofertas de trabajo de Workana, con notificaciones por Telegram y Email, filtrado por tiempo y modo de monitoreo en tiempo real.
# Huntly — Workana Job Scraper & Assistant

Un scraper y pipeline para detectar ofertas en Workana, generar propuestas y enviar notificaciones (Telegram / Email). Este repositorio fue reorganizado en paquetes para facilitar extensión y despliegue.

**Resumen rápido:**
- Scrapea ofertas desde Workana.
- Persiste resultados en `data/` (CSV, JSON y SQLite).
- Integra generación de propuestas (AI) y envío automatizado.
- Notificaciones por Telegram y (opcional) Email.

**Estructura principal del repo**
- **`huntly/`**: paquete principal con submódulos:
  - `huntly/core` — almacenamiento, notificaciones y utilidades.
  - `huntly/workana` — scraper, sender (playwright) y bootstrap de sesión.
  - `huntly/integrations` — integraciones (Telegram bot).
  - `huntly/pipeline` — pipeline de propuestas y procesamiento.
  - `huntly/ai` — generación de propuestas (OpenAI u otra API).
- **`config/`**: archivos de configuración y ejemplo de entorno.
- **`data/`**: datos generados y persistencia (`workana_jobs.csv`, `workana_jobs.json`, `jobs.db`).

**Archivos importantes**: [config/.env.example](config/.env.example), [main.py](main.py), [data/workana_jobs.csv](data/workana_jobs.csv), [data/workana_jobs.json](data/workana_jobs.json), [data/jobs.db](data/jobs.db)

---

**Requisitos recomendados**
- Python 3.11 o 3.12 (probado). Algunas dependencias como Playwright pueden requerir herramientas de sistema.
- Instala dependencias desde `requirements.txt`.

Instalación y entorno
```bash
python -m venv .venv
.venv\\Scripts\\activate    # Windows (PowerShell/CMD)
pip install -r requirements.txt
```

Configuración inicial
 - Copia el ejemplo de entorno y edítalo:
```powershell
copy config\\.env.example config\\.env   # Windows
```
 - Valores importantes (en `config/.env`):
   - `WORKANA_URL`: URL de búsqueda en Workana.
   - `WORKANA_STATE_FILE`: archivo para Playwright storage state (por defecto `config/workana_state.json`).
   - `CSV_FILE` / `JSON_FILE`: si solo das un nombre se guardará en `data/`.
   - `TG_TOKEN`, `TG_CHAT`: para notificaciones por Telegram.
   - `OPENAI_API_KEY` (opcional): para generación automática de propuestas.

Inicio por primera vez
1. Guardar sesión de Playwright (solo si usas envío automático):

```powershell
python -m huntly.workana.bootstrap
# Sigue las instrucciones en la ventana del navegador para iniciar sesión en Workana
```

El bootstrap guardará `WORKANA_STATE_FILE` (por defecto `config/workana_state.json`).

2. Ejecutar la aplicación principal (bot + scraper):

```powershell
python main.py
```

`main.py` arranca el bot de Telegram en un hilo y ejecuta el scraper/pipeline en primer plano.

Modo desarrollo y pruebas
 - Ejecutar solo el scraper:
```bash
python -m huntly.workana.scraper
```
 - Ejecutar solo el bot (útil para desarrollo):
```bash
python -m huntly.integrations.telegram_bot
```

Persistencia y archivos generados
- Todos los archivos generados por defecto se almacenan en la carpeta `data/`:
  - `data/workana_jobs.csv` — CSV principal.
  - `data/workana_jobs.json` — respaldo JSON.
  - `data/jobs.db` — SQLite para estados y metadatos.

Si prefieres otra ruta, configura las variables `CSV_FILE`, `JSON_FILE` o `DB_FILE` en `config/.env`.

Notas operativas
- `config/.env` se carga desde `huntly/__init__.py`; no subas credenciales al control de versiones.
- Evitamos ejecutar efectos secundarios en import time; los scripts tienen `if __name__ == '__main__'` o se ejecutan con `-m`.
- Si mueves o renuevas la sesión de Playwright, actualiza `WORKANA_STATE_FILE`.

Depuración
- Logs se imprimen en consola; para más detalle ajusta el nivel de logging en `config/.env` o dentro de `huntly/core`.

Contribuir
- Si quieres colaborar: abre un issue con la propuesta o un PR siguiendo el estilo del repositorio.

Licencia
- Revisa el archivo `LICENSE` en la raíz.

Contacto
- Mantenedor: @constadinisio

---

Si quieres, puedo:
- Añadir una sección de ejemplo de `config/.env` con todos los valores por defecto.
- Añadir un script `make`/`ps1` para inicializar el entorno y bootstrap automático.
