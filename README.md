# Workana Job Scraper 🚀

Un scraper robusto y automatizado para extraer ofertas de trabajo de Workana, con notificaciones por Telegram y Email, filtrado por tiempo y modo de monitoreo en tiempo real.

## ✨ Características
- **Scraping Inteligente:** Extrae títulos, presupuestos, fechas y enlaces directamente de Workana.
- **Notificaciones:** Recibe alertas instantáneas en Telegram o por Email cuando aparece un nuevo trabajo.
- **Modo Watch:** Mantén el scraper corriendo 24/7 para no perderte ninguna oportunidad.
- **Filtrado por Tiempo:** Filtra trabajos muy antiguos para enfocarte solo en lo reciente.
- **Persistencia:** Guarda los resultados en archivos CSV y JSON para su análisis posterior.

---

## 🛠️ Instalación

1. **Clonar el repositorio** (o descargar los archivos):
   ```bash
   git clone <url-del-repo>
   cd workana_scrapper
   ```

2. **Crear y activar un entorno virtual** (Recomendado):
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Mac/Linux:
   source .venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuración (.env)

El sistema utiliza un archivo `.env` para manejar la configuración de forma segura. 

1. Copia el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```
2. Abre el archivo `.env` y completa tus datos:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `URL` | URL de Workana con tus filtros de búsqueda | `https://www.workana.com/jobs?skills=python` |
| `MAX_AGE_HOURS` | Solo procesar trabajos de las últimas X horas | `3.0` |
| `NOTIFY_TELEGRAM` | Activar/Desactivar Telegram | `true` |
| `TG_TOKEN` | Token de tu bot de Telegram | `123456:ABC-DEF...` |
| `TG_CHAT` | ID de tu chat o grupo | `6461819551` |
| `NOTIFY_EMAIL` | Activar/Desactivar Email | `false` |
| `WATCH_MODE` | Ejecutar continuamente | `true` |
| `INTERVAL_MINUTES` | Minutos entre chequeos en modo Watch | `10` |

### 🤖 Cómo crear tu Bot de Telegram
1. Busca a `@BotFather` en Telegram y envíale `/newbot`.
2. Sigue los pasos para obtener tu `TG_TOKEN`.
3. Para obtener tu `TG_CHAT` ID, puedes usar el bot `@userinfobot` o enviarle un mensaje a tu nuevo bot y revisar la URL: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`.

---

## 🚀 Uso

### Ejecución Única
```bash
python workana_scraper.py
```

### Modo Monitoreo (Watch Mode)
Puedes activarlo en el `.env` (`WATCH_MODE=true`) o por consola:
```bash
python workana_scraper.py --watch --interval 15
```

### Probar Telegram
Verifica que tu configuración de Telegram sea correcta:
```bash
python test_telegram.py
```

---

## 📄 Archivos Generados
- `workana_jobs.csv`: Base de datos principal de trabajos encontrados.
- `workana_jobs.json`: Respaldo en formato JSON.
- `.env`: Tu configuración personal (¡No subir a GitHub!).

---
*Desarrollado por [@constadinisio](https://github.com/constadinisio)*
