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
---
### Escenario 2: prueba de escalamiento rápido
| Parámetro | Valor |
|-----------|-------|
| **Herramienta** | Locust 2.15+ |
| **Tipo de prueba** | Ramp test |
| **Estrategia de carga** | 100 usuarios a 600 |
| **Duración de fase** | 3 minutos de ramp up y 5 minutos sostenidos|
---
### Escenario 3: prueba sostenida
| Parámetro | Valor |
|-----------|-------|
| **Herramienta** | Locust 2.15+ |
| **Tipo de prueba** | Stability test |
| **Estrategia de carga** | 480 usuarios |
| **Duración de fase** | 3 minutos de ramp up y 5 minutos sostenidos|
---
## Resultados Escenario 1
A continuación, se muestran los resultados del escenario 1. En este se realizó la revisión de sanidad del sistema. En la siguiente imagen se muestra la tabla de resumen obtenida con locust en donde se puede ver que no se tiene ningún error en las peticiones realizadas y que el tiempo de respuesta promedio es de 983 ms. Con esto, la prueba cumple con su objetivo de permitir la primera revisión de la capa web. 
![resumen sanity](capaWeb/sanity/sanity_smoke.png)

Adicionalmente, se incluyen las gráficas de Locust con las que se puede ver el incremento a 5 usuarios y el flujo de peticiones por segundo y tiempos de respuesta. Con estas visualizaciones se puede ver que hay un comportamiento exitoso de la aplicación en una primera instancia. 

![charts sanity](capaWeb/sanity/sanity_charts.png)
---
## Resultados Escenario 2

### Casos sin escalado

![charts ramp 100](capaWeb/Ramp/chart100uses.png)
![charts ramp 200](capaWeb/Ramp/200_ns_graph.png)

### Casos con escalado

![charts ramp 600](capaWeb/Ramp/chart600.png)
---
## Resultados Escenario 3
A partir del escenario anterior, se determinó que el punto en el que el degradamiento es considerable es al llegar a los 600 usuarios. Es por esto que para esta prueba se utiliza el 80% de esa capacidad, llegando así a 480 usuarios. Los resultados de este escenario se presentan a continuación. 

![resumen sostenida](capaWeb/sostenida/480-users.png)

![charts sostenida](capaWeb/sostenida/400-charts.png)

---

## Análisis de Resultados

### Punto de Saturación
**900 usuarios concurrentes** es el límite observado donde:
-  Tasa de éxito: **95.50%** (cumple SLO ≥ 90%)
-  Tiempo promedio: **21,000 ms** (excede SLO de 20,000 ms por 5%)
-  Throughput máximo: **45 req/s**

### Punto Óptimo Recomendado
**600-750 usuarios concurrentes** representa el balance ideal:
-  Tasa de éxito: **94.50-95.00%**
-  Tiempo promedio: **19,000-20,000 ms** (dentro del SLO)
-  Throughput: **30-37.5 req/s**
-  Margen de seguridad: 20% bajo capacidad máxima

### Degradación Observada
- **30-300 usuarios:** Alta tasa de fallos (10% → 7%), estabilización progresiva
- **300-750 usuarios:** Sistema estable, tasa de fallos mejora consistentemente
- **750-900 usuarios:** Sistema en límite, degradación leve pero controlada

---

## Resumen — Capacidad de la Capa Web (Plan A)

| Métrica | Valor |
|---------|-------|
| **Capacidad máxima experimental** | 600 usuarios concurrentes |
| **Capacidad sostenible (recomendada)** |480 usuarios concurrentes |
| **Punto de degradación** |  |
| **Throughput máximo sostenido** |  |
| **Tasa de error en capacidad sostenible** |  |
| **Tiempo promedio en capacidad sostenible** |   |

**Conclusión:**  
El sistema con **auto scaling habilitado** soporta hasta **900 usuarios concurrentes**, pero la capacidad recomendada es **600-750 usuarios** para mantener tiempos de respuesta dentro del SLO de 20 segundos. La mejora progresiva en la tasa de éxito (90% → 95.5%) demuestra que el **auto scaling responde efectivamente** a la carga creciente.

