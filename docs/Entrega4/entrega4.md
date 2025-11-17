# Entrega 4 - Escalabilidad en la Capa Worker

## 📋 Descripción General

Implementación de **escalabilidad automática para workers** en la plataforma ANB Video, utilizando **Amazon SQS** como sistema de mensajería y configurando **Auto Scaling**. Se migró de RabbitMQ/Redis a SQS para aprovechar la infraestructura gestionada de AWS y la capacidad de autoscaling. Además se configuró alta disponibilidad multi zona.

---

## 🎯 Cambios Principales vs. Entrega 3

| Aspecto | Entrega 3 | Entrega 4 |
|---------|-----------|-----------|
| **Mensajería** | RabbitMQ (EC2) + Redis | Amazon SQS |
| **Worker Scaling** | Manual (1 instancia fija) | Auto Scaling Group (1-3 instancias) |
| **Backend Scaling** | Auto Scaling (1-3 instancias) | Auto Scaling (1-3 instancias) |
| **Alta Disponibilidad** | Single-AZ | Multi-AZ (us-east-1a, us-east-1b) |
| **Sistema de Colas** | Celery tasks | SQS Producer/Consumer directo |
| **Monitoreo Workers** | CloudWatch | CloudWatch + métricas de cola SQS |

---

## Arquitectura AWS Actualizada

### Vista General

![Arquitectura AWS](images/architecture_aws.png)

La arquitectura ahora incorpora los siguientes componentes:

#### **1. Application Load Balancer (ALB) - Multi-AZ**
- **Zonas de Disponibilidad:** us-east-1a y us-east-1b
- **Función:** Distribuir tráfico HTTP/HTTPS entre instancias backend
- **Target Groups:** Instancias distribuidas en ambas AZs

#### **2. Auto Scaling Group (Backend API)**
- **Instancias:** t3.micro (2 vCPU, 1 GiB RAM)
- **Configuración:**
  - Min: 1 instancia
  - Max: 3 instancias
- **Contenido:**
  - FastAPI application
  - SQS Producer (envía mensajes)

#### **3. Auto Scaling Group (Workers)**
- **Instancias:** t3.medium (2 vCPU, 4 GB RAM)
- **Configuración:**
  - Min: 1 instancia
  - Max: 3 instancias
- **Contenido:**
  - Worker SQS Consumer
  - Procesamiento de videos
  - Storage Temporal: `/tmp/anb-temp`

#### **4. Amazon SQS (Sistema de Mensajería)**
- **Tipo:** Standard Queue
- **Nombre:** `processing-queue`
- **Región:** us-east-1
- **Configuración:**
  - Visibility Timeout: 300 segundos (5 minutos)
  - Message Retention: 4 días
  - Receive Wait Time: 20 segundos (long polling)
  - Max Message Size: 256 KB

#### **5. Amazon S3 (Storage)**
- **Bucket:** `anb-video-storage-2025`
- **Región:** us-east-1
- **Estructura:**
  ```
  s3://anb-video-storage-2025/
  ├── uploads/          # Videos sin procesar
  ├── processed/        # Videos procesados (720p)
  └── resources/        # Assets estáticos (logos)
  ```
- Sin cambios respecto a Entrega 3

#### **6. RDS PostgreSQL (Base de Datos)**
- **Instancia:** db.t3.micro
- **Multi-AZ:** Habilitado
- Sin cambios respecto a Entrega 3

---

## Diagrama de Componentes

![Componentes](images/components_aws.png)

**Cambios Clave:**

### Producer (Backend API)
- Reemplazado encolado de Celery por SQS Producer
- Clase `SQSMessageProducer` en `app/core/message_producer.py`
- Envía mensajes JSON con metadatos del video a procesar
- Crea cola automáticamente si no existe

### Consumer (Workers)
- Clase `SQSProcessWorker` en `app/tasks/video_tasks.py`
- Long polling (20s) para reducir llamadas a API
- Eliminación automática de mensajes procesados
- Manejo de errores con reintentos automáticos de SQS

**Ventajas vs. RabbitMQ/Redis:**
- Totalmente gestionado 
- Escalabilidad 
- Aumento en la disponibilidad
- Integración nativa con CloudWatch para Auto Scaling
- Costos por uso (sin servidores 24/7)

---

## Flujo de Procesamiento con SQS

![Flujo](images/video_processing_flow_s3.png)

### Fase 1: Upload y Encolado

1. Usuario sube video via ALB → Backend API
2. Backend valida y guarda en S3 (`uploads/`)
3. Backend crea registro en RDS (status: `uploaded`)
4. **Backend envía mensaje a SQS:**
   ```json
   {
     "video_id": "uuid-123",
     "file_path": "uploads/uuid-123.mp4",
     "status": "pending",
     "timestamp": "2025-11-16T10:30:00Z"
   }
   ```
5. Backend responde 202 Accepted al usuario

### Fase 2: Procesamiento Asíncrono

1. Worker consume mensaje de SQS (long polling)
2. Worker actualiza status → `processing` en RDS
3. Worker descarga video de S3
4. Worker procesa con MoviePy/FFmpeg:
   - Resize 
   - Trim 
   - Agrega watermark, intro y outro
5. Worker sube video procesado a S3 (`processed/`)
6. Worker actualiza status → `processed` en RDS
7. **Worker elimina mensaje de SQS** (confirmación de procesamiento)
8. Worker limpia archivos temporales

---

## Secuencia de Procesamiento

![Secuencia](images/sequence.png)

---

## Auto Scaling de Workers

### Políticas Configuradas

#### Scale Out (Agregar Workers)
```yaml
Trigger: ApproximateNumberOfMessages > 10
Duration: 3 minutos consecutivos
Action: Agregar 1 instancia
Cooldown: 300 segundos
```

#### Scale In (Remover Workers)
```yaml
Trigger: ApproximateNumberOfMessages < 3
Duration: 5 minutos consecutivos
Action: Remover 1 instancia
Cooldown: 600 segundos
```

---

## Alta Disponibilidad Multi-AZ

### Configuración

- **ALB Subnets:** 
  - `subnet-us-east-1a` (pública)
  - `subnet-us-east-1b` (pública)

### Ventajas

- Tolerancia a fallas de zona de disponibilidad
- Mantenimiento sin downtime
- Latencia reducida para usuarios en diferentes regiones (proyectada)

---

## Conclusiones

### Mejoras Implementadas

1. **Escalabilidad de Workers:** Auto Scaling basado en tamaño de cola SQS
2. **Alta Disponibilidad:** Multi-AZ para backend y workers
3. **Mensajería Gestionada:** SQS reemplaza infraestructura propia
4. **Reducción de Costos:** Eliminación de instancias RabbitMQ/Redis 24/7

### Próximos Pasos

- Implementar Dead Letter Queue (DLQ) para mensajes fallidos
- Configurar SNS notifications para alertas críticas
- Optimizar políticas de scaling basadas en pruebas de carga

---
