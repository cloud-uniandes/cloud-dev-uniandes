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
| **Web API (Auto Scaled)** | ECS Fargate<br>Min: 1, Max: 3 | FastAPI + Nginx |
| **Worker** | ECS Fargate<br>Min: 1, Max: 3 | Celery + FFmpeg |
| **Message Queue** | Amazon SQS FIFO | Cola de tareas asíncronas |
| **Base de Datos** | RDS PostgreSQL db.t3.micro Multi-AZ | Metadatos y estado |
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
- **Tiempo promedio de respuesta** ≤ 10,000 ms
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
| **Estrategia de carga** | 80% de máxima carga de usuarios |
| **Duración de fase** | 3 minutos de ramp up y 5 minutos sostenidos|
---
## Resultados Escenario 1
A continuación, se muestran los resultados del escenario 1. En este se realizó la revisión de sanidad del sistema. En la siguiente imagen se muestra la tabla de resumen obtenida con locust en donde se puede ver que no se tiene ningún error en las peticiones realizadas y que el tiempo de respuesta promedio es de 983 ms. Con esto, la prueba cumple con su objetivo de permitir la primera revisión de la capa web. 
![resumen sanity](capaWeb/sanity/sanity_smoke.png)

Adicionalmente, se incluyen las gráficas de Locust con las que se puede ver el incremento a 5 usuarios y el flujo de peticiones por segundo y tiempos de respuesta. Con estas visualizaciones se puede ver que hay un comportamiento exitoso de la aplicación en una primera instancia. 

![charts sanity](capaWeb/sanity/sanity_charts.png)
---
## Resultados Escenario 2
Dentro del segundo escenario se realizó una evaluación del sistema en cuanto a la cantidad de usuarios concurrentes que soporta antes de presentarse degradación en el sistema. Este proceso se realizó primeramente sobre el servicio sin opción de autoescalado y luego con opción de escalado hasta 3 instancias. Esto permite ver el desempeño general del sistema y comprobar el uso de autoescalamiento para aumentar el nivel de carga que puede manejar. 
### Casos sin escalado
Dentro del caso sin escalado se probó el desempeño con 100 y 200 usuarios concurrentes. A continuación, se presentan las gráficas de peiticiones por segundo, tiempo de respuesta y número de usuarios. 
Por el lado de la gráfica de 100 usuarios, se puede ver que hay una degradación del sistema cuando se tienen los 100 usuarios de forma concurrente. Esto hace que el número de fallos y el tiempo por petición incremente a medida que se mantienen los usuarios. 
![charts ramp 100](capaWeb/Ramp/chart100uses.png)
Asimismo, se puede ver que en el momento en el que se tienen los 200 usuarios de forma concurrente se degrada considerablemente el sistema y su desempeño. 
![charts ramp 200](capaWeb/Ramp/200_ns_graph.png)
Para comparar más fácilmente, se presenta la tabla con las métricas principales obtenidas de estas pruebas. 
| **Cantidad de usuarios** | **Cantidad de peticiones** | **Cantidad Fallos** | **Porcentaje de fallo** | **Tiempo promedio (ms)** | **Tiempo máximo (ms)** | **Req/s**  | **Failures/s** |
|--------------------------|----------------------------|---------------------|-------------------------|--------------------------|------------------------|------------|----------------|
| 100                      | 1709                       | 105                 | 6%                      | 6101.07                  | 42850.797              | 9.4954     | 0.5834         |
| 200                      | 4192                       | 291                 | 7%                      | 6858.22                  | 104631.838             | 13.97      | 0.9702         |

Como se puede ver al tener una única instancia se genera una degradación mucho más rápido comparado con los resultados encontrados dentro de las pruebas de la entrega pasada. 
### **Casos con escalado**
Los resultados sin escalado soportan una baja carga de usuarios, por lo que se probó la aplicación al activar autoescalamiento hasta 3 tasks. Con esto se revisó el comportamiento del sistema nuevamente. A continuación, se presenta una tabla con los resultados para diferentes niveles de usuarios. 
| **Cantidad de usuarios** | **Cantidad de peticiones** | **Cantidad Fallos** | **Porcentaje de fallo** | **Tiempo promedio (ms)** | **Tiempo máximo (ms)** | **Req/s**  | **Failures/s** |
|--------------------------|----------------------------|---------------------|-------------------------|--------------------------|------------------------|------------|----------------|
| 200                      | 5357                       | 12                  | 0.22%                   | 5507.32                  | 102207.2715            | 17.86      | 0.04           |
| 400                      | 8705                       | 11                  | 0.13%                   | 6828.117                 | 81645.514              | 28.9814    | 0.037          |
| 500                      | 6683                       | 170                 | 2.54%                   | 9549.010                 | 102846.3386            | 22.26      | 0.56           |
| 600                      | 8934                       | 480                 | 5.37%                   | 10195.8259               | 62443.8                | 29.723     | 1.597          |

Como se puede ver el punto de degradación en donde la aplicación deja de cumplir con los requisitos propuestso de contar con un error de peticiones menor al 5% y un tiempo de respuesta menor a los 10 segundos. Al comparar esto con los resultados de la entrega pasada se puede ver que para la misma cantida de usuarios hay mejorías en cuanto al tiempo promedio, el cual es casi la mitad. Sin embargo, el comportamiento del sistema en cuanto a porcentaje de fallos se mantiene similar. Esto hace ver que los cambios generados permiten un nivel de atención similar pero que resulta mucho más rápido que en escenarios pasados. 
Finalmente, se presentan las gráficas de Locust para el punto de 600 usuarios. Nuevamente, se puede ver que la degradación del sistema sucede en el punto en el que hay mayor concurrencia de usuarios y el sistema lleva un tiempo de establecimiento. En este punto, es donde hay un pico en cuanto a los tiempos de respuesta, las peticiones y los fallos que se generan. 

![charts ramp 600](capaWeb/Ramp/chart600.png)
---
## Resultados Escenario 3
A partir del escenario anterior, se determinó que el punto en el que el degradamiento es considerable es al llegar a los 600 usuarios. Es por esto que para esta prueba se utiliza el 80% de esa capacidad, llegando así a 480 usuarios. Los resultados de este escenario se presentan a continuación. Para esto, se presenta la tabla de resumen de las métricas de Locust en donde se resalta que se generó un erorr únicamente del 2%, y un tiempo promedio de 10 segundos. Asimismo, se resalta que la cantidad de peticiones por segundo es de 25.  

![resumen sostenida](capaWeb/sostenida/480-users.png)
La gráfica de las pruebas para una carga de 480 usuarios se puede ver como el sistema se mantiene de forma estable a lo largo del desarrollo de las pruebas. Hay picos en donde se ve el aumento de tiempos. Pero, sin embargo, se puede ver que el sistema es estable con este tipo de carga y se desempeña de manera adecuada cumpliendo los requerimientos de desempeño establecidos dentro del plan de capacidad. 

![charts sostenida](capaWeb/sostenida/400-charts.png)

---

## Análisis de Resultados

### Punto de Saturación
**600 usuarios concurrentes** es el límite observado donde:
-  Tasa de éxito: **94.63%** 
-  Tiempo promedio: **10,195 ms** 
-  Throughput máximo: **29.75 req/s**

### Punto Óptimo Recomendado
**480 usuarios concurrentes** representa el balance ideal:
-  Tasa de éxito: **97.69%**
-  Tiempo promedio: **10,300 ms** 
-  Throughput: **25 req/s**
-  Margen de seguridad: 20% bajo capacidad máxima

### Degradación Observada
- **100-400 usuarios:** Pocos fallos, sistema estable bajo esta carga. 
- **400-500 usuarios:** Sistema estable dentro de los limites definidos.
- **600+ usuarios:** Sistema en límite, degradación fuera de los límites establecidos.

---

**Conclusión:**  
El sistema con **auto scaling habilitado** soporta hasta **600 usuarios concurrentes**, pero la capacidad recomendada es **480 usuarios** para mantener tiempos de respuesta dentro del SLO de 10 segundos. Como se puede ver, el uso de auto scaling es vital, puesto que sin este no se logra mantener una carga superior a los 100 usuarios concurrentes. 


