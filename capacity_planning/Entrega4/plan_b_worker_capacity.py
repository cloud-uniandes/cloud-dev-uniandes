"""
Plan B: Pruebas de capacidad del Worker (videos/min)
Inyecta tareas directamente en Redis sin modificar código de la app.
"""
import redis
import json
import uuid
import time
import os
import asyncio
import asyncpg
from datetime import datetime, timezone
from typing import List, Dict
import statistics

# Configuración
REDIS_HOST = os.getenv("REDIS_HOST", "172.31.X.X")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

DB_HOST = os.getenv("DB_HOST", "172.31.X.X")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "anb_user")
DB_PASS = os.getenv("DB_PASS", "password")
DB_NAME = os.getenv("DB_NAME", "anb_db")

S3_BUCKET = os.getenv("S3_BUCKET", "anb-video-storage-2025")

# Tamaños de video
VIDEO_SIZES = {
    "50MB": "uploads/test_50mb.mp4",
    "100MB": "uploads/test_100mb.mp4",
}


class WorkerLoadTester:
    """Pruebas de carga para el Worker inyectando tareas en Redis"""
    
    def __init__(self):
        self.redis_client = None
        self.db_pool = None
        self.results = []
        self.test_user_id = None
    
    async def connect(self):
        """Conectar a Redis y PostgreSQL"""
        # Conectar a Redis
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=False  # Importante para Celery
        )
        
        # Probar conexión
        self.redis_client.ping()
        print(f"✅ Conectado a Redis: {REDIS_HOST}:{REDIS_PORT}")
        
        # Conectar a PostgreSQL
        self.db_pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            min_size=5,
            max_size=20
        )
        print(f"✅ Conectado a PostgreSQL: {DB_HOST}:{DB_PORT}")
        
        # Obtener o crear usuario de prueba
        await self.ensure_test_user()
    
    async def ensure_test_user(self):
        """Asegurar que existe un usuario de prueba"""
        async with self.db_pool.acquire() as conn:
            # Intentar obtener usuario existente
            user = await conn.fetchrow("""
                SELECT id FROM users 
                WHERE username = 'loadtest_user'
                LIMIT 1
            """)
            
            if user:
                self.test_user_id = user['id']
            else:
                # Crear usuario si no existe
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                hashed = pwd_context.hash("LoadTest123!")
                
                user_id = await conn.fetchval("""
                    INSERT INTO users (username, email, password_hash)
                    VALUES ('loadtest_user', 'loadtest@anb.com', $1)
                    RETURNING id
                """, hashed)
                
                self.test_user_id = user_id
            
            print(f"✅ Usuario de prueba: {self.test_user_id}")
    
    async def create_video_record(self, video_id: str, file_path: str) -> Dict:
        """Crea un registro de video en la BD"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO videos (id, title, file_path, status, user_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO NOTHING
            """,
            uuid.UUID(video_id),
            f"Load Test - {video_id[:8]}",
            file_path,
            "uploaded",
            self.test_user_id,
            datetime.now(timezone.utc),
            datetime.now(timezone.utc)
            )
        
        return {
            "id": video_id,
            "file_path": file_path,
            "created_at": datetime.now(timezone.utc)
        }
    
    def inject_celery_task(self, video_id: str, file_path: str) -> str:
        """
        Inyecta una tarea Celery directamente en Redis.
        
        Formato de mensaje Celery v4+:
        https://docs.celeryproject.org/en/stable/internals/protocol.html
        """
        task_id = str(uuid.uuid4())
        
        # Payload de tarea Celery
        message = {
            "body": json.dumps([
                [],  # args
                {
                    "video_id": video_id,
                    "temp_file_path": file_path
                },  # kwargs
                {
                    "callbacks": None,
                    "errbacks": None,
                    "chain": None,
                    "chord": None
                }
            ]).encode('utf-8'),
            "content-encoding": "utf-8",
            "content-type": "application/json",
            "headers": {
                "lang": "py",
                "task": "app.tasks.video_tasks.process_video_task",
                "id": task_id,
                "root_id": task_id,
                "parent_id": None,
                "group": None,
                "meth": None,
                "shadow": None,
                "eta": None,
                "expires": None,
                "retries": 0,
                "timelimit": [None, None],
                "argsrepr": "[]",
                "kwargsrepr": f"{{'video_id': '{video_id}', 'temp_file_path': '{file_path}'}}",
            },
            "properties": {
                "correlation_id": task_id,
                "reply_to": str(uuid.uuid4()),
                "delivery_mode": 2,
                "delivery_info": {
                    "exchange": "",
                    "routing_key": "celery"
                },
                "priority": 0,
                "body_encoding": "base64",
                "delivery_tag": str(uuid.uuid4())
            }
        }
        
        # Serializar mensaje completo
        serialized = json.dumps(message).encode('utf-8')
        
        # Enviar a Redis (cola Celery)
        self.redis_client.lpush("celery", serialized)
        
        print(f"📤 Task injected: {task_id[:8]}... → {file_path}")
        return task_id
    
    async def monitor_video_processing(self, video_ids: List[str], timeout_minutes: int = 10) -> Dict:
        """Monitorea el procesamiento de videos en la BD"""
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        processed = set()
        failed = set()
        processing_times = []
        
        print(f"\n👀 Monitoreando {len(video_ids)} videos...")
        
        while len(processed) + len(failed) < len(video_ids):
            # Timeout
            if time.time() - start_time > timeout_seconds:
                print(f"⏱️  Timeout alcanzado ({timeout_minutes} min)")
                break
            
            # Consultar estado en BD
            async with self.db_pool.acquire() as conn:
                results = await conn.fetch("""
                    SELECT id::text, status, created_at, updated_at
                    FROM videos
                    WHERE id = ANY($1::uuid[])
                """, [uuid.UUID(vid) for vid in video_ids])
                
                for row in results:
                    vid = row['id']
                    status = row['status']
                    
                    if vid not in processed and vid not in failed:
                        if status == 'processed':
                            proc_time = (row['updated_at'] - row['created_at']).total_seconds()
                            processing_times.append(proc_time)
                            processed.add(vid)
                            print(f"✅ {vid[:8]}... processed in {proc_time:.1f}s")
                        
                        elif status == 'failed':
                            failed.add(vid)
                            print(f"❌ {vid[:8]}... failed")
            
            # Esperar antes de siguiente consulta
            await asyncio.sleep(2)
            
            # Mostrar progreso cada 10 segundos
            elapsed = time.time() - start_time
            if int(elapsed) % 10 == 0:
                throughput = len(processed) / (elapsed / 60) if elapsed > 0 else 0
                print(f"📊 Progress: {len(processed)}/{len(video_ids)} processed | "
                      f"{len(failed)} failed | {throughput:.2f} videos/min")
        
        # Calcular métricas finales
        total_time = time.time() - start_time
        
        result = {
            "total_videos": len(video_ids),
            "processed": len(processed),
            "failed": len(failed),
            "pending": len(video_ids) - len(processed) - len(failed),
            "total_time_minutes": total_time / 60,
            "throughput_videos_per_minute": len(processed) / (total_time / 60) if total_time > 0 else 0,
            "avg_processing_time_seconds": statistics.mean(processing_times) if processing_times else 0,
            "p50_processing_time": statistics.median(processing_times) if processing_times else 0,
            "p95_processing_time": statistics.quantiles(processing_times, n=20)[18] if len(processing_times) > 20 else 0,
        }
        
        return result
    
    async def test_saturation(self, num_videos: int, size_label: str):
        """
        Prueba de saturación: inyectar N videos de golpe
        """
        print(f"\n{'='*80}")
        print(f"🔥 SATURACIÓN: {num_videos} videos ({size_label})")
        print(f"{'='*80}")
        
        file_path = VIDEO_SIZES[size_label]
        video_ids = []
        
        # Inyectar todas las tareas
        for i in range(num_videos):
            video_id = str(uuid.uuid4())
            
            # Crear registro en BD
            await self.create_video_record(video_id, file_path)
            
            # Inyectar tarea en Redis
            self.inject_celery_task(video_id, file_path)
            
            video_ids.append(video_id)
        
        print(f"✅ {num_videos} tareas inyectadas")
        
        # Monitorear procesamiento
        result = await self.monitor_video_processing(video_ids, timeout_minutes=15)
        
        # Guardar resultado
        result['test_type'] = 'saturation'
        result['size'] = size_label
        result['num_videos'] = num_videos
        self.results.append(result)
        
        # Mostrar resultado
        self.print_result(result)
        
        return result
    
    async def test_sustained(self, videos_per_minute: int, duration_minutes: int, size_label: str):
        """
        Prueba sostenida: mantener X videos/min durante Y minutos
        """
        print(f"\n{'='*80}")
        print(f"🔄 SOSTENIDA: {videos_per_minute} videos/min × {duration_minutes} min ({size_label})")
        print(f"{'='*80}")
        
        file_path = VIDEO_SIZES[size_label]
        total_videos = videos_per_minute * duration_minutes
        interval = 60.0 / videos_per_minute
        
        video_ids = []
        start_time = time.time()
        
        for i in range(total_videos):
            video_id = str(uuid.uuid4())
            
            # Crear registro en BD
            await self.create_video_record(video_id, file_path)
            
            # Inyectar tarea
            self.inject_celery_task(video_id, file_path)
            
            video_ids.append(video_id)
            
            # Esperar intervalo
            await asyncio.sleep(interval)
            
            if (i + 1) % videos_per_minute == 0:
                elapsed = time.time() - start_time
                print(f"✅ {i + 1}/{total_videos} inyectados ({elapsed/60:.1f} min)")
        
        print(f"✅ {total_videos} tareas inyectadas")
        
        # Monitorear procesamiento
        result = await self.monitor_video_processing(video_ids, timeout_minutes=duration_minutes + 10)
        
        # Guardar resultado
        result['test_type'] = 'sustained'
        result['size'] = size_label
        result['videos_per_minute'] = videos_per_minute
        result['duration_minutes'] = duration_minutes
        self.results.append(result)
        
        # Mostrar resultado
        self.print_result(result)
        
        return result
    
    def print_result(self, result: Dict):
        """Imprime resultados de una prueba"""
        print(f"\n{'='*80}")
        print(f"✅ RESULTADO - {result['size']} ({result['test_type'].upper()})")
        print(f"{'='*80}")
        print(f"  Videos procesados:    {result['processed']}/{result['total_videos']} ({result['processed']/result['total_videos']*100:.1f}%)")
        print(f"  Videos fallidos:      {result['failed']}")
        print(f"  Videos pendientes:    {result['pending']}")
        print(f"  Tiempo total:         {result['total_time_minutes']:.2f} min")
        print(f"  Throughput:           {result['throughput_videos_per_minute']:.2f} videos/min")
        print(f"  Tiempo promedio:      {result['avg_processing_time_seconds']:.2f}s")
        print(f"  p50 tiempo:           {result['p50_processing_time']:.2f}s")
        print(f"  p95 tiempo:           {result['p95_processing_time']:.2f}s")
        print(f"{'='*80}\n")
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        await self.connect()
        
        # Pruebas de saturación
        await self.test_saturation(num_videos=10, size_label="50MB")
        await asyncio.sleep(60)  # Esperar entre pruebas
        
        await self.test_saturation(num_videos=10, size_label="100MB")
        await asyncio.sleep(60)
        
        # Pruebas sostenidas
        await self.test_sustained(videos_per_minute=5, duration_minutes=3, size_label="50MB")
        await asyncio.sleep(60)
        
        await self.test_sustained(videos_per_minute=5, duration_minutes=3, size_label="100MB")
        
        # Cerrar conexiones
        await self.db_pool.close()
        self.redis_client.close()
        
        # Resumen final
        self.print_summary()
    
    def print_summary(self):
        """Imprime resumen de todas las pruebas"""
        print(f"\n{'='*80}")
        print(f"📊 RESUMEN FINAL - PLAN B")
        print(f"{'='*80}\n")
        
        for result in self.results:
            print(f"{result['size']} ({result['test_type']}):")
            print(f"  Throughput: {result['throughput_videos_per_minute']:.2f} videos/min")
            print(f"  Éxito: {result['processed']}/{result['total_videos']} ({result['processed']/result['total_videos']*100:.1f}%)")
            print()
        
        print(f"{'='*80}\n")


# Ejecutar pruebas
if __name__ == "__main__":
    tester = WorkerLoadTester()
    asyncio.run(tester.run_all_tests())