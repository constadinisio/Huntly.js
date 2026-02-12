# 🚀 Despliegue de Huntly en Railway

Guía completa para desplegar Huntly en [Railway.app](https://railway.app), una plataforma que soporta aplicaciones Python con Playwright y procesos de larga duración.

## 📋 Requisitos Previos

- Cuenta en [Railway.app](https://railway.app) (gratis para empezar)
- Cuenta de GitHub con el repositorio Huntly
- Bot de Telegram configurado (ver README principal)
- (Opcional) API key de OpenAI

---

## 🎯 Pasos de Despliegue

### 1. Preparar el Repositorio

Asegúrate de que tu repositorio tenga los siguientes archivos (ya incluidos):

- ✅ `Procfile` - Define el comando de inicio
- ✅ `runtime.txt` - Especifica Python 3.11
- ✅ `railway.json` - Configuración de Railway
- ✅ `nixpacks.toml` - Configuración de build con Playwright
- ✅ `requirements.txt` - Dependencias Python

**Sube los cambios a GitHub:**

```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 2. Crear Proyecto en Railway

1. Ve a [railway.app](https://railway.app) y haz login con GitHub
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Autoriza Railway para acceder a tus repositorios
5. Selecciona el repositorio **Huntly.js**
6. Railway detectará automáticamente que es un proyecto Python

### 3. Configurar Variables de Entorno

En el dashboard de Railway, ve a la pestaña **"Variables"** y agrega:

#### Variables Obligatorias

```env
WORKANA_URL=https://www.workana.com/jobs?category=it-programming&subcategory=web-development
TG_TOKEN=tu_token_de_telegram_aqui
TG_CHAT=tu_chat_id_aqui
```

#### Variables Opcionales

```env
OPENAI_API_KEY=sk-tu_api_key_aqui
CSV_FILE=workana_jobs.csv
JSON_FILE=workana_jobs.json
DB_FILE=jobs.db
WORKANA_STATE_FILE=config/workana_state.json
```

> [!TIP]
> Puedes copiar los valores desde tu archivo local `config/.env`

### 4. Configurar Volumen Persistente (Recomendado)

Para que los datos no se pierdan en cada redeploy:

1. En Railway, ve a **"Settings"** → **"Volumes"**
2. Click en **"Add Volume"**
3. Configura:
   - **Mount Path**: `/app/data`
   - **Size**: 1 GB (suficiente para SQLite y CSVs)
4. Guarda los cambios

### 5. Desplegar

1. Railway comenzará el build automáticamente
2. Espera a que complete (puede tomar 3-5 minutos la primera vez)
3. Revisa los logs en la pestaña **"Deployments"**

**Logs esperados:**

```
✓ Installing Python 3.11
✓ Installing dependencies from requirements.txt
✓ Installing Playwright Chromium
✓ Installing Chromium system dependencies
✓ Starting application: python main.py
```

---

## ⚙️ Configuración Inicial de Playwright

> [!WARNING]
> **Importante**: La sesión de Playwright (`workana_state.json`) debe configurarse manualmente.

### Opción A: Usando Railway CLI (Recomendado)

1. Instala Railway CLI:

```bash
npm i -g @railway/cli
```

2. Login en Railway:

```bash
railway login
```

3. Vincula tu proyecto:

```bash
railway link
```

4. Ejecuta el bootstrap remotamente:

```bash
railway run python -m huntly.workana.bootstrap
```

5. Sigue las instrucciones en el navegador para iniciar sesión en Workana

### Opción B: Subir Archivo Manualmente

1. Ejecuta el bootstrap localmente:

```bash
python -m huntly.workana.bootstrap
```

2. Esto genera `config/workana_state.json`

3. Sube el archivo a Railway usando Railway CLI:

```bash
railway shell
# Dentro del shell:
mkdir -p config
# Luego copia el contenido de tu archivo local al remoto
```

O configura una variable de entorno `WORKANA_STATE_JSON` con el contenido del archivo.

---

## 📊 Verificación del Despliegue

### 1. Revisar Logs

En Railway dashboard → **"Deployments"** → Click en el último deploy → **"View Logs"**

**Logs exitosos:**

```
✓ Telegram bot started
✓ Scraper initialized
✓ Monitoring Workana for new jobs...
```

### 2. Probar el Bot de Telegram

1. Abre Telegram y busca tu bot
2. Envía un mensaje de prueba
3. El bot debe responder (si está configurado para ello)

### 3. Verificar Scraping

- Espera unos minutos
- Deberías recibir notificaciones de nuevas ofertas en Telegram
- Revisa los logs para confirmar que el scraper está funcionando

---

## 🔧 Troubleshooting

### Error: "Playwright browser not found"

**Solución**: Verifica que `nixpacks.toml` incluya:

```toml
[phases.install]
cmds = [
  "pip install -r requirements.txt",
  "playwright install chromium",
  "playwright install-deps chromium"
]
```

### Error: "Telegram bot token invalid"

**Solución**: Verifica que `TG_TOKEN` esté correctamente configurado en Variables de Railway.

### Error: "Out of memory"

**Solución**: Chromium consume memoria. Actualiza a un plan con más RAM:

1. Railway → **"Settings"** → **"Resources"**
2. Aumenta la memoria a al menos **1 GB**

### Los datos se pierden en cada deploy

**Solución**: Configura un volumen persistente (ver paso 4).

### El scraper no encuentra nuevas ofertas

**Solución**: 

1. Verifica que `WORKANA_URL` sea correcta
2. Revisa los logs para errores de scraping
3. Confirma que el filtro de tiempo esté configurado correctamente

---

## 💰 Costos Estimados

Railway ofrece:

- **Plan Hobby**: $5/mes de crédito gratis
- **Uso típico de Huntly**: ~$3-5/mes (con 1GB RAM)
- **Plan Developer**: $10/mes (incluye más recursos)

> [!NOTE]
> El plan gratuito es suficiente para empezar y probar la aplicación.

---

## 🔄 Actualizaciones

Para actualizar la aplicación:

1. Haz cambios en tu código local
2. Commit y push a GitHub:

```bash
git add .
git commit -m "Update feature X"
git push origin main
```

3. Railway detectará el cambio y redesplegará automáticamente

---

## 📱 Monitoreo

Railway proporciona:

- **Logs en tiempo real**: Dashboard → Deployments → View Logs
- **Métricas**: CPU, RAM, Network usage
- **Alertas**: Configura notificaciones por email

---

## 🆘 Soporte

Si tienes problemas:

1. Revisa los logs en Railway
2. Consulta la [documentación de Railway](https://docs.railway.app)
3. Abre un issue en el repositorio de GitHub
4. Contacta al mantenedor: @constadinisio

---

## ✅ Checklist de Despliegue

- [ ] Repositorio subido a GitHub con archivos de configuración
- [ ] Cuenta creada en Railway.app
- [ ] Proyecto creado y vinculado al repositorio
- [ ] Variables de entorno configuradas
- [ ] Volumen persistente configurado (opcional pero recomendado)
- [ ] Build completado exitosamente
- [ ] Sesión de Playwright configurada (bootstrap)
- [ ] Bot de Telegram respondiendo
- [ ] Scraper detectando ofertas
- [ ] Notificaciones llegando correctamente

---

**¡Listo!** 🎉 Huntly ahora está corriendo 24/7 en Railway.
