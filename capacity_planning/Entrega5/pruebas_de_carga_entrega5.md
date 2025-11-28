# Pruebas de Capacidad - Entrega 5
---

## Objetivo General

Evaluar la **capacidad máxima y estabilidad** del sistema bajo condiciones de carga progresivas con la nueva arquitectura de **mensajería asíncrona (SQS)** y **auto scaling**, identificando:

- El **punto de saturación** de la capa web (usuarios concurrentes)
- La **degradación del tiempo de respuesta** bajo cargas crecientes
- Los **recursos críticos** (CPU, memoria, cola SQS, red)
- El **comportamiento del auto scaling** bajo diferentes cargas

---

## Infraestructura Evaluada

| Componente | Especificación | Función |
|------------|----------------|---------|
| **Load Balancer** | AWS ELB Application | Distribución de tráfico HTTP |
| **Web API (Sin escalado)** | ECS Fargate<br>Min: 1, Max: 3 | FastAPI + Nginx |
| **Web API (Auto Scaled)** | ECS Fargate<br>Min: 1, Max: 3 | FastAPI + Nginx |
| **Worker** | ECS Fargate<br>Min: 1, Max: 3 | Celery + FFmpeg |
| **Message Queue** | Amazon SQS FIFO | Cola de tareas asíncronas |
| **Base de Datos** | RDS PostgreSQL db.t3.micro Multi-AZ | Metadatos y estado |
| **Cache** | ElastiCache Redis | Results backend |
| **Storage** | Amazon S3 | Almacenamiento de videos |
| **Monitoreo** | AWS CloudWatch + Auto Scaling Policies | Métricas y alarmas |

---

## Cambios Arquitectónicos vs Entrega 4

| Aspecto | Entrega 4 | Entrega 5 |
|---------|-----------|-----------|
| **Capa Worker** | Instancias EC2 | Uso de ECS Fargate |
| **Capa API** | Instancias EC2 | Uso de ECS Fargate |
---

# Plan A: Capacidad de la Capa Web 

---

## Objetivo del Escenario

Determinar el número máximo de **usuarios concurrentes** que la API de subida soporta cumpliendo los SLOs:
- **Tiempo promedio de respuesta** ≤ ms
- **Tasa de error (4xx/5xx)** ≤ 5%
- **Sin degradación progresiva** en pruebas sostenidas

---

## Configuración de la Prueba

Para el desarrollo de estas pruebas se contemplaron 3 escenarios. El primer escenario consistió en una prueba de sanidad con la que se pretendía revisar el comportamiento básico del sistema. El segundo escenario consiste en una prueba de escalamiento rápido en donde se genera un incremento en la cantidad de usuarios concurrentes. Finalmente, se realizó una prueba sostenida en donde se mantuvo la ejecución por 5 minutos con el 80% de la carga encontrada como máxima en el anterior escenario. Estas pruebas fueron realizadas con Locust usando el archivo `capaWeb/plan_a_web_capacity.py`. Este archivo es una variación del utilizado en la entrega 4 en donde se redefine la URL de la aplicación y se agregan los endpoints faltantes para una prueba más completa.  
### Escenario 1: prueba de sanidad 
| Parámetro | Valor |
|-----------|-------|
| **Herramienta** | Locust 2.15+ |
| **Tipo de prueba** | Smoke Test |
| **Estrategia de carga** | 5 usuarios permamentes |
| **Duración por fase** | 1 minuto|
### Escenario 2: prueba de escalamiento rápido
| Parámetro | Valor |
|-----------|-------|
| **Herramienta** | Locust 2.15+ |
| **Tipo de prueba** | Ramp test |
| **Estrategia de carga** | 100 usuarios a 600 |
| **Duración de fase** | 3 minutos de ramp up y 5 minutos sostenidos|

### Escenario 3: prueba sostenida
| Parámetro | Valor |
|-----------|-------|
| **Herramienta** | Locust 2.15+ |
| **Tipo de prueba** | Stability test |
| **Estrategia de carga** | 480 usuarios |
| **Duración de fase** | 3 minutos de ramp up y 5 minutos sostenidos|
---
## Resultados Escenario 1

