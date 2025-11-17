# 🏀 ANB Rising Stars API REST
# Integrantes
- Wyo Hann Chu Mendez
- Maria Alejandra Angulo
- Pablo Pedreros Diaz
- Laura Murcia
# Entrega 1
[Video sustentacion](https://uniandes-my.sharepoint.com/:v:/g/personal/ma_angulom1_uniandes_edu_co/EUhPYPMCi5xIv7JGx64JxkABr23pE_VLKCyAn_p0FLIZug?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=ZePOFZ)
# Entrega 2
[Video sustentación](https://uniandes-my.sharepoint.com/:v:/g/personal/l_murciac_uniandes_edu_co/Efouc0l1MaNHniZvdXIYpucBjdqri1SCB7MhIOwO4jwvlw?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=S0OR3U)
[Documentación](https://github.com/cloud-uniandes/cloud-dev-uniandes/blob/main/docs/Entrega2/entrega2.md)
# Entrega 4
[Video Sustentación](https://uniandes-my.sharepoint.com/:v:/g/personal/l_murciac_uniandes_edu_co/IQBAjCxuZxiyR4OxQYQBIU37AfYrvV1SYiRC9oP4VrFSvhE?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D&e=crDgNz)

[Documentación](https://github.com/cloud-uniandes/cloud-dev-uniandes/blob/main/docs/Entrega4/entrega4.md)

---
API REST completa para la plataforma ANB Rising Stars Showcase - Sistema de carga de videos y votación para jugadores de baloncesto.

[![Tests](https://img.shields.io/badge/tests-34%2F34%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-75%25-brightgreen)](htmlcov/)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688)](https://fastapi.tiangolo.com/)

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Stack Tecnológico](#️-stack-tecnológico)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación-completa)
- [Configuración](#-configuración)
- [Uso del API](#-uso-del-api)
- [Testing](#-testing-y-validación)
- [Docker](#despliegue-con-docker)
- [Scripts Útiles](#-scripts-útiles)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Métricas del Proyecto](#-métricas-del-proyecto)
- [Solución de Problemas](#-solución-de-problemas)
- [Notas de Desarrollo](#-notas-de-desarrollo)

---


## 📖 Descripción despliegue local

Esta es una API REST completa basada en **FastAPI** que permite a jugadores de baloncesto subir videos de sus habilidades, y a los fans votar por sus favoritos. La documentación técnica del proyecto se encuentra a continuación:

[Documentación Técnica](https://github.com/ChusitooXDuwu/cloud-dev-uniandes/blob/9a67a16be7679b311d567cac2dc0d34ddbec21df/docs/README.md)

### El sistema incluye:

- ✅ **9 endpoints REST** completamente funcionales
- ✅ **Autenticación** de usuarios (signup/login)
- ✅ **Carga y gestión** de videos con validación (**probado con videos reales**)
- ✅ **Sistema de votación** (un voto por usuario por video)
- ✅ **Rankings dinámicos** con filtro por ciudad
- ✅ **34 tests automatizados** (incluyendo upload real de videos)
- ✅ **Documentación Swagger** automática
- ✅ **Colección de Postman** incluida

---

## ✨ Características

| Característica | Descripción |
|----------------|-------------|
| 🔐 **Autenticación** | Signup/Login simplificado (sin JWT para desarrollo) |
| 📹 **Validación de videos** | MP4, 20-60s, mínimo 1080p con FFprobe |
| 📝 **Gestión de videos** | Listar, ver detalles, eliminar (con permisos) |
| 🌍 **Videos públicos** | Con paginación y filtros |
| 🗳️ **Sistema de votación** | Prevención de votos duplicados |
| 🏆 **Rankings** | Ordenados por votos con filtro por ciudad |
| ⚡ **Operaciones async** | SQLAlchemy asíncrono para mejor rendimiento |
| 💾 **Almacenamiento** | Local filesystem (preparado para cloud) |
| 🧪 **Testing completo** | Pytest (30 tests) + Newman + Swagger UI |

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **Backend** | Python | 3.13 | Lenguaje principal |
| **Framework** | FastAPI | 0.115.0 | Framework web async |
| **Base de Datos** | PostgreSQL | 17+ | Base de datos relacional |
| **ORM** | SQLAlchemy | 2.0.36 | ORM async |
| **Migraciones** | Alembic | 1.14.0 | Control de versiones de BD |
| **Validación** | Pydantic | 2.10.5 | Validación de datos |
| **Tareas Asíncronas** | Celery | 5.5.1 | Sistema de colas para tareas |
| **Broker** | RabbitMQ | 3.13.7 | Broker de mensajería para las tareas que se redirigen a Celery |
| **Seguridad** | Bcrypt | 4.2.1 | Hashing de contraseñas |
| **Testing** | Pytest | 8.3.4 | Framework de testing |
| **Servidor** | Uvicorn | 0.32.0 | Servidor ASGI |
| **Video** | FFmpeg | - | Validación de videos |

---

## 📦 Requisitos Previos

Antes de comenzar, necesitas tener instalado:

- ✅ **Python 3.10+** → [Descargar](https://www.python.org/downloads/)
- ✅ **PostgreSQL 12+** → [Descargar](https://www.postgresql.org/download/)
- ✅ **FFmpeg** → [Descargar](https://ffmpeg.org/download.html)
- ✅ **Node.js y npm** (opcional, para Newman) → [Descargar](https://nodejs.org/)
- ✅ **Git** (opcional) → [Descargar](https://git-scm.com/)

---

## 🚀 Instalación Completa

### Paso 1: Clonar el Repositorio

```bash
# Con Git
git clone <url-del-repositorio>
cd cloud-dev-uniandes

# O descargar el ZIP y extraer
```

### Paso 2: Instalar Python

1. Descargar Python 3.10+ desde https://www.python.org/downloads/
2. **IMPORTANTE**: Durante la instalación, marcar **"Add Python to PATH"**
3. Verificar instalación:

```bash
python --version
# Debería mostrar: Python 3.10.x o superior
```

### Paso 3: Instalar PostgreSQL

#### 🪟 Windows:
1. Descargar desde https://www.postgresql.org/download/windows/
2. Ejecutar el instalador
3. **Recordar** la contraseña del usuario `postgres`
4. Puerto por defecto: `5432`

#### 🍎 Mac:
```bash
brew install postgresql
brew services start postgresql
```

#### 🐧 Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Paso 4: Crear Bases de Datos

Abrir **SQL Shell (psql)** o **pgAdmin** y ejecutar:

```sql
-- Crear la base de datos principal
CREATE DATABASE anb_db;

-- Crear el usuario
CREATE USER anb_user WITH PASSWORD 'anb_pass';

-- Dar permisos a anb_db
GRANT ALL PRIVILEGES ON DATABASE anb_db TO anb_user;

-- Crear base de datos de pruebas
CREATE DATABASE anb_db_test;
GRANT ALL PRIVILEGES ON DATABASE anb_db_test TO anb_user;

-- Conectar a anb_db y dar permisos al esquema public
\c anb_db
GRANT ALL ON SCHEMA public TO anb_user;

-- Conectar a anb_db_test y dar permisos al esquema public
\c anb_db_test
GRANT ALL ON SCHEMA public TO anb_user;

-- Salir
\q
```

### Paso 5: Instalar FFmpeg

#### 🪟 Windows:
1. Descargar desde https://ffmpeg.org/download.html
2. Extraer el archivo ZIP
3. Agregar la carpeta `bin` al PATH:
   - Buscar "Variables de entorno" en Windows
   - Editar la variable `Path`
   - Agregar la ruta completa a `ffmpeg\bin`
4. **Reiniciar la terminal**
5. Verificar: `ffmpeg -version`

#### 🍎 Mac:
```bash
brew install ffmpeg
```

#### 🐧 Linux:
```bash
sudo apt-get install ffmpeg
```

### Paso 6: Crear Entorno Virtual

```bash
# Windows
python -m venv venv

# Linux/Mac
python3 -m venv venv
```

### Paso 7: Activar Entorno Virtual

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

💡 **Nota**: Deberías ver `(venv)` al inicio de tu línea de comandos.

### Paso 8: Instalar Dependencias

```bash
pip install -r requirements.txt
```

⏱️ Esto puede tomar 2-5 minutos dependiendo de tu conexión.

### Paso 9: Configurar Variables de Entorno

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

**NO es necesario editar `.env`** si usaste las credenciales por defecto (`anb_user`/`anb_pass`).

El archivo `.env` contiene:
```env
DATABASE_URL=postgresql+asyncpg://anb_user:anb_pass@localhost:5432/anb_db
STORAGE_PATH=./storage
MAX_FILE_SIZE_MB=100
```

📁 **Nota sobre `storage/`**: Las carpetas para archivos (`storage/uploads/`, `storage/processed/`, `storage/temp/`) **se crean automáticamente** al iniciar la aplicación. No necesitas crearlas manualmente.

### Paso 10: Ejecutar Migraciones

```bash
alembic upgrade head
```

✅ Deberías ver:
```
INFO  [alembic.runtime.migration] Running upgrade  -> b139fb2ec928, Initial migration: users, videos, votes
```


### Iniciar el Servidor

 1. Dependencias
Se agregaron Celery, Kombu y Gevent al `requirements.txt` para soporte de tareas asíncronas y compatibilidad con Windows.

 2. Configuración de Celery
Se creó `app/core/celery_app.py` con la configuración del broker RabbitMQ (pyamqp://guest:guest@localhost//).

 3. Tarea Asíncrona de Procesamiento
Se implementó `process_video_task` en `app/tasks/video_tasks.py` que:
- Cambia el estado del video a "processing"
- Valida el video con FFprobe (duración y resolución)
- Mueve el archivo de `uploads/` a `processed/`
- Actualiza el estado del video a "processed" o "failed"

 4. Modificación del Endpoint de Upload
Se modificó el endpoint `/api/videos/upload` para:
- Realizar validaciones rápidas (tipo, tamaño)
- Guardar el video con estado "uploaded"
- Encolar la tarea de procesamiento con `.delay()`
- Retornar inmediatamente sin esperar el procesamiento

 5. Compatibilidad con Windows
Se creó una versión síncrona de `validate_video_sync()` en `app/utils/video_validator.py` ya que Celery no soporta funciones async directamente.

 **Pendiente**
Procesamiento real del video: Actualmente solo se copia el archivo. Falta implementar el corte del video y agregar banner al final (marcado como `# TO_DO`).

---

### Comandos para Ejecutar con queues

 1. Iniciar RabbitMQ
```bash
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

 2. Iniciar FastAPI
```bash
uvicorn app.main:app --reload --port 8000
```

 3. Iniciar Celery Worker (nueva terminal)

**Windows:**
```bash
celery -A app.core.celery_app worker --pool=solo --loglevel=info
```

**Linux/Mac:**
```bash
celery -A app.core.celery_app worker --loglevel=info
```

> **Nota:** En Windows es obligatorio usar `--pool=solo` o `--pool=gevent` debido a problemas de compatibilidad de Celery con multiprocessing en Windows.


✅ Si todo está correcto, verás:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Application startup complete.
```

### Paso 12: Verificar Instalación

Abre tu navegador y visita:

- 🏥 **Health Check**: http://localhost:8000/health
- 📚 **Documentación**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc

Si ves la documentación de Swagger, **¡todo está funcionando!** 🎉

---

## ⚙️ Configuración

### Estructura de `.env`

```env
# Base de Datos
DATABASE_URL=postgresql+asyncpg://usuario:contraseña@host:puerto/database

# Almacenamiento
STORAGE_PATH=./storage

# Límites
MAX_FILE_SIZE_MB=100

# Aplicación
APP_NAME=ANB Rising Stars API
APP_VERSION=1.0.0
```

### Configuración Personalizada

Si necesitas usar credenciales diferentes:

1. Editar `.env`
2. Cambiar `DATABASE_URL` con tus credenciales
3. Reiniciar el servidor

---

## 📡 Uso del API

### 🔗 URLs Disponibles

| URL | Descripción |
|-----|-------------|
| http://localhost:8000 | API principal |
| http://localhost:8000/health | Health check |
| **http://localhost:8000/docs** | **Documentación Swagger UI** ⭐ |
| http://localhost:8000/redoc | Documentación ReDoc |

### 📋 Los 9 Endpoints

| # | Método | Endpoint | Descripción |
|---|--------|----------|-------------|
| 1 | POST | `/api/auth/signup` | Registrar nuevo usuario |
| 2 | POST | `/api/auth/login` | Iniciar sesión |
| 3 | POST | `/api/videos/upload` | Subir video (MP4, validado) |
| 4 | GET | `/api/videos` | Listar videos del usuario |
| 5 | GET | `/api/videos/{video_id}` | Ver detalle de un video |
| 6 | DELETE | `/api/videos/{video_id}` | Eliminar video |
| 7 | GET | `/api/public/videos` | Listar videos públicos |
| 8 | POST | `/api/public/videos/{video_id}/vote` | Votar por un video |
| 9 | GET | `/api/public/rankings` | Ver rankings por votos |

### 🎮 Cómo Probar el API

#### Opción 1: Swagger UI (Recomendado) ⭐

1. Ir a http://localhost:8000/docs
2. Click en cualquier endpoint
3. Click en **"Try it out"**
4. Completar los parámetros
5. Click en **"Execute"**
6. Ver la respuesta

#### Opción 2: Postman

1. Abrir Postman
2. Importar `collections/anb_api_complete.postman_collection.json`
3. Importar `collections/postman_environment.json`
4. Seleccionar el environment "ANB Development"
5. Ejecutar los requests (21 requests con todos los casos de éxito y error)

#### Opción 3: cURL

```bash
# 1. Crear un usuario
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan@example.com",
    "password1": "SecurePass123",
    "password2": "SecurePass123",
    "city": "Bogotá",
    "country": "Colombia"
  }'

# 2. Iniciar sesión
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan@example.com",
    "password": "SecurePass123"
  }'

# 3. Listar videos públicos
curl http://localhost:8000/api/public/videos?limit=10&offset=0

# 4. Ver rankings
curl http://localhost:8000/api/public/rankings?limit=10
```

---

## 🧪 Testing y Validación

El proyecto ha sido validado con **3 métodos diferentes** para asegurar que todos los endpoints funcionan correctamente.

### ✅ Método 1: Pytest (Principal)

**34 tests automatizados** cubriendo todos los endpoints y casos de uso, **incluyendo upload real de videos**.

```bash
# Ejecutar todos los tests
pytest

# Tests con output detallado
pytest -v

# Tests con cobertura de código
pytest --cov=app --cov-report=term-missing

# Generar reporte HTML de cobertura
pytest --cov=app --cov-report=html
# Luego abrir: htmlcov/index.html

# Tests específicos
pytest tests/test_auth.py          # Solo autenticación
pytest tests/test_videos.py        # Solo videos (incluyendo upload)
pytest tests/test_votes.py         # Solo votación
pytest tests/test_rankings.py      # Solo rankings

# Probar solo el upload
pytest tests/test_videos.py::TestVideos::test_upload_video_success -v
```

**Resultado esperado:**
```
============================== test session starts ==============================
collected 34 items

tests/test_auth.py::TestAuth::test_signup_success PASSED                  [  3%]
tests/test_videos.py::TestVideos::test_upload_video_success PASSED        [  6%]
tests/test_videos.py::TestVideos::test_upload_video_missing_file PASSED   [  9%]
tests/test_videos.py::TestVideos::test_upload_video_invalid_user_id PASSED [ 12%]
tests/test_videos.py::TestVideos::test_upload_video_wrong_format PASSED   [ 15%]
... (34 tests total)

======================= 34 passed in XX.XXs =======================
```

**📹 Video de Prueba**: Los tests usan un video MP4 real (`tests/test_data/flex.mp4`) para validar completamente el endpoint de upload.

### ✅ Método 2: Newman (CLI de Postman)

Newman ejecuta las colecciones de Postman desde la línea de comandos.

**Instalación:**
```bash
# Instalar Newman globalmente (requiere Node.js)
npm install -g newman

# Verificar instalación
newman --version
```

**Ejecución:**
```bash
# Asegurarse de que el servidor esté corriendo
uvicorn app.main:app --reload --port 8000

# En otra terminal, ejecutar Newman
newman run collections/anb_api_complete.postman_collection.json \
  -e collections/postman_environment.json \
  --color on
```

**Resultado esperado:**
```
┌─────────────────────────┬────────────────────┬────────────────────┐
│                         │           executed │             failed │
├─────────────────────────┼────────────────────┼────────────────────┤
│              iterations │                  1 │                  0 │
│                requests │                 21 │                  0 │
│            test-scripts │                 21 │                  0 │
│              assertions │                 45 │                  0 │
└─────────────────────────┴────────────────────┴────────────────────┘
```

**✅ Resultado Newman:**
- ✅ **45/45 assertions pasando (100%)**
- ✅ 21 requests ejecutados correctamente
- ✅ Todos los casos de éxito y error validados
- ✅ Incluye: signup, login, upload, publish, vote, delete, rankings
- ✅ Video de prueba: `tests/test_data/flex.mp4`

### ✅ Método 3: Prueba Manual del Upload

#### Opción A: Script Python

```bash
# Asegúrate de que el servidor esté corriendo
uvicorn app.main:app --reload --port 8000

# En otra terminal
python test_upload_manual.py
```

Este script:
1. Crea un usuario de prueba
2. Sube el video `flex.mp4`
3. Verifica que el video se guardó correctamente

#### Opción B: Swagger UI

1. Ir a http://localhost:8000/docs
2. Expandir **POST /api/videos/upload**
3. Click en **"Try it out"**
4. Llenar los campos:
   - `video_file`: Seleccionar archivo MP4 (usa `tests/test_data/flex.mp4`)
   - `title`: "Mi Video de Prueba"
   - `user_id`: (usar un UUID de usuario existente)
5. Click en **"Execute"**
6. Verificar respuesta 201 con `video_id`

#### Opción C: cURL

```bash
# Primero crear un usuario y obtener su ID
USER_ID=$(curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Test","last_name":"User","email":"test@example.com","password1":"Pass123","password2":"Pass123","city":"Bogotá","country":"Colombia"}' \
  | jq -r '.user_id')

# Subir video
curl -X POST http://localhost:8000/api/videos/upload \
  -F "video_file=@tests/test_data/flex.mp4" \
  -F "title=Mi Video de Prueba" \
  -F "user_id=$USER_ID"
```

---

## Despliegue con Docker

Para correr la aplicación ya dockerizada corra para un ambiente estable. 

```docker build --no-cache -t anb_app:latest .```

```docker compose up -d```

```docker compose ps```

```docker compose logs -f app```

---

## 🎯 Scripts Útiles

### Comandos Rápidos

```bash
# Activar entorno virtual
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac

# Iniciar servidor
uvicorn app.main:app --reload --port 8000

# Ejecutar tests
pytest -v

# Ver cobertura
pytest --cov=app --cov-report=html

# Crear migración nueva
alembic revision --autogenerate -m "Descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1

# Ver estado de migraciones
alembic current

# Ver historial de migraciones
alembic history
```

### Script de Inicio Rápido (Windows)

Crear `start.bat`:
```batch
@echo off
call venv\Scripts\activate.bat
uvicorn app.main:app --reload --port 8000
```

### Script de Inicio Rápido (Linux/Mac)

Crear `start.sh`:
```bash
#!/bin/bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

```bash
chmod +x start.sh
./start.sh
```

---

## 📁 Estructura del Proyecto

```
cloud-dev-uniandes/
├── 📁 app/                          # Código principal
│   ├── 📁 api/v1/                   # Endpoints del API
│   │   ├── __init__.py
│   │   ├── auth.py                  # Signup, Login
│   │   ├── videos.py                # Upload, List, Get, Delete
│   │   └── public.py                # Public videos, Vote, Rankings
│   ├── 📁 core/                     # Configuración
│   │   ├── __init__.py
│   │   ├── config.py                # Settings (variables de entorno)
│   │   └── exceptions.py            # Excepciones personalizadas
│   ├── 📁 models/                   # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py                  # Modelo User
│   │   ├── video.py                 # Modelo Video
│   │   └── vote.py                  # Modelo Vote
│   ├── 📁 schemas/                  # Schemas Pydantic
│   │   ├── __init__.py
│   │   ├── user.py                  # Validación de usuarios
│   │   ├── video.py                 # Validación de videos
│   │   └── vote.py                  # Validación de votos
│   ├── 📁 repositories/             # Repository Pattern
│   │   ├── __init__.py
│   │   ├── user_repository.py       # CRUD de usuarios
│   │   ├── video_repository.py      # CRUD de videos
│   │   └── vote_repository.py       # CRUD de votos
│   ├── 📁 storage/                  # Almacenamiento
│   │   ├── __init__.py
│   │   └── local_storage.py         # Storage local
│   ├── 📁 utils/                    # Utilidades
│   │   ├── __init__.py
│   │   ├── security.py              # Bcrypt hashing
│   │   └── video_validator.py      # Validación con FFprobe
│   ├── 📁 db/                       # Base de datos
│   │   ├── __init__.py
│   │   ├── base.py                  # Declarative base
│   │   └── session.py               # Async session
│   └── main.py                      # FastAPI app
├── 📁 tests/                        # Tests (30 tests)
│   ├── __init__.py
│   ├── conftest.py                  # Fixtures
│   ├── test_auth.py                 # 7 tests
│   ├── test_videos.py               # 10 tests
│   ├── test_votes.py                # 5 tests
│   └── test_rankings.py             # 8 tests
├── 📁 alembic/                      # Migraciones
│   ├── versions/
│   │   └── b139fb2ec928_initial_migration.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── 📁 collections/                  # Postman
│   ├── anb_api_complete.postman_collection.json  # 21 requests completos
│   └── postman_environment.json
├── 📁 storage/                      # Archivos
│   ├── uploads/                     # Videos subidos
│   └── processed/                   # Videos procesados
├── 📄 requirements.txt              # Dependencias Python
├── 📄 .env                          # Variables de entorno (no en Git)
├── 📄 .env.example                  # Plantilla de .env
├── 📄 .gitignore                    # Archivos ignorados
├── 📄 alembic.ini                   # Config de Alembic
├── 📄 pytest.ini                    # Config de Pytest
└── 📄 README.md                     # Este archivo
```

---

## 📊 Métricas del Proyecto

### Código
- **Archivos creados**: 96 archivos
- **Líneas de código**: ~3,000+ líneas
- **Modelos de datos**: 3 (User, Video, Vote)
- **Endpoints**: 9 completamente funcionales
- **Repositorios**: 3 (Repository Pattern)

### Testing
- **Tests totales**: 34
- **Tests pasando**: 34 (100%)
- **Tests de upload real**: 4 (usando video MP4 real)
- **Cobertura de código**: ~75%
- **Tipos de tests**: Unit + Integration + Upload Real

### Validación Triple
| Método | Tests/Assertions | Resultado |
|--------|------------------|-----------|
| **Pytest** | 34/34 tests | ✅ 100% (incluyendo upload real) |
| **Newman** | 18-20/26 assertions | ✅ 69% (limitación conocida) |
| **Swagger UI** | 9/9 endpoints | ✅ 100% |
| **Script Manual** | Upload + Validación | ✅ 100% |

### Base de Datos
- **Tablas**: 3 (users, videos, votes)
- **Relaciones**: Foreign keys + UniqueConstraints
- **Índices**: En email, user_id, is_public, votes_count
- **Migraciones**: 1 migración inicial aplicada

---

## 🔧 Solución de Problemas

### ❌ Error: "uvicorn not recognized"

**Problema**: Entorno virtual no activado

**Solución**:
```bash
# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate

# Verificar que ves (venv) al inicio de la línea de comandos
```

### ❌ Error: "Database connection failed"

**Problema**: PostgreSQL no está corriendo o credenciales incorrectas

**Solución**:
```bash
# 1. Verificar que PostgreSQL esté corriendo
# Windows
Get-Service postgresql*

# Linux/Mac
sudo systemctl status postgresql

# 2. Verificar credenciales en .env
# 3. Verificar que la BD exista
psql -U postgres
\l  # Listar bases de datos
```

### ❌ Error: "ffprobe not found"

**Problema**: FFmpeg no instalado o no en PATH

**Solución**:
1. Instalar FFmpeg (ver Paso 5)
2. Agregar al PATH
3. **Reiniciar la terminal**
4. Verificar: `ffmpeg -version`

### ❌ Error: "Permission denied" (PowerShell)

**Problema**: Política de ejecución de PowerShell

**Solución**:
```powershell
# Como Administrador
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego activar entorno virtual
.\venv\Scripts\Activate.ps1
```

### ❌ Error: "Port 8000 already in use"

**Problema**: Otro proceso está usando el puerto

**Solución**:
```bash
# Opción 1: Usar otro puerto
uvicorn app.main:app --reload --port 8001

# Opción 2: Encontrar proceso en puerto 8000
# Windows
Get-NetTCPConnection -LocalPort 8000

# Linux/Mac
lsof -i :8000

# Opción 3: Detener servidor anterior
# Presionar Ctrl+C en la terminal del servidor
```

### ❌ Tests fallan con error de BD

**Problema**: Base de datos de tests no existe

**Solución**:
```sql
-- En psql
CREATE DATABASE anb_db_test;
GRANT ALL PRIVILEGES ON DATABASE anb_db_test TO anb_user;
\c anb_db_test
GRANT ALL ON SCHEMA public TO anb_user;
```

### ❌ Import errors después de instalar

**Problema**: Instalación incompleta o entorno no activado

**Solución**:
```bash
# 1. Verificar entorno virtual activado
# 2. Actualizar pip
pip install --upgrade pip

# 3. Reinstalar dependencias
pip install -r requirements.txt
```

---

## 💡 Notas de Desarrollo

### ⚠️ Simplificaciones para Desarrollo

Este proyecto usa algunas simplificaciones para facilitar el desarrollo:

1. **Autenticación**: Se usa `user_id` en parámetros en lugar de JWT tokens
   - ✅ **Desarrollo**: Más simple y rápido

2. **Almacenamiento**: Filesystem local
   - ✅ **Desarrollo**: Simple y sin costos
   - ⚠️ **Producción**: Migrar a S3, GCS, o Azure Blob Storage

3. **Base de Datos**: PostgreSQL local
   - ✅ **Desarrollo**: Instalación local
   - ⚠️ **Producción**: Usar servicio administrado (AWS RDS, etc.)

### 🔐 Seguridad

- ✅ Contraseñas hasheadas con Bcrypt
- ✅ Validación de inputs con Pydantic
- ✅ Protección contra SQL injection (SQLAlchemy ORM)
- ✅ Validación de archivos (tipo, tamaño, duración)
- ⚠️ Sin rate limiting (agregar en producción)
- ⚠️ Sin HTTPS (usar en producción)

### 📝 Validaciones Implementadas

#### Videos:
- Formato: MP4
- Tamaño máximo: 100MB
- Duración: 20-60 segundos
- Resolución: Mínimo 1080p (altura >= 1080 píxeles)

#### Usuarios:
- Email único y válido
- Contraseñas deben coincidir
- Todos los campos requeridos

#### Votación:
- Un voto por usuario por video
- Solo videos públicos pueden recibir votos
- Usuario debe existir

---

## 📚 Recursos Adicionales

### Documentación del API

- **Swagger UI**: http://localhost:8000/docs (interactivo)
- **ReDoc**: http://localhost:8000/redoc (documentación limpia)
- **OpenAPI JSON**: http://localhost:8000/openapi.json (spec)

### Guías Específicas

- **Postman**: Ver `collections/README.md` para guía completa
- **Testing**: Revisar archivos en `tests/` para ejemplos
- **Modelos**: Ver archivos en `app/models/` para estructura de BD

### Enlaces Útiles

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [Pytest Docs](https://docs.pytest.org/)

---

## ✅ Checklist de Verificación

Antes de considerar el proyecto completo, verificar:

- [ ] PostgreSQL instalado y corriendo
- [ ] Base de datos `anb_db` creada
- [ ] Base de datos `anb_db_test` creada
- [ ] FFmpeg instalado y en PATH
- [ ] Entorno virtual creado
- [ ] Dependencias instaladas
- [ ] Archivo `.env` configurado
- [ ] Migraciones aplicadas
- [ ] Servidor inicia sin errores
- [ ] Tests pasan (`pytest -v`)
- [ ] Swagger UI accesible
- [ ] Health check responde

---

## 🤝 Contribuir

Si deseas contribuir al proyecto:

1. Fork el repositorio
2. Crear una rama: `git checkout -b feature/nueva-funcionalidad`
3. Hacer cambios y agregar tests
4. Ejecutar tests: `pytest -v`
5. Commit: `git commit -m "Agregar nueva funcionalidad"`
6. Push: `git push origin feature/nueva-funcionalidad`
7. Crear Pull Request

---

## 🎓 Información del Proyecto

- **Nombre**: ANB Rising Stars API REST
- **Curso**: Cloud Development - Universidad de los Andes
- **Fecha**: Octubre 2025
- **Versión**: 1.0.0
- **Licencia**: Proyecto académico

---

## 📞 Soporte

¿Tienes problemas o preguntas?

1. Revisar la sección [Solución de Problemas](#-solución-de-problemas)
2. Verificar el [Checklist de Verificación](#-checklist-de-verificación)
3. Consultar la documentación en http://localhost:8000/docs
4. Abrir un issue en el repositorio

---

## 🎉 ¡Listo para Usar!

Si llegaste hasta aquí y todos los pasos funcionaron:

1. **Ve a** http://localhost:8000/docs
2. **Explora** los 9 endpoints en Swagger UI
3. **Prueba** crear un usuario y subir un video
4. **Ejecuta** los tests con `pytest -v`
5. **Disfruta** tu API REST completamente funcional! 🚀

---

**⭐ ¡Proyecto completado exitosamente con 30/30 tests pasando y 70% de cobertura!**

