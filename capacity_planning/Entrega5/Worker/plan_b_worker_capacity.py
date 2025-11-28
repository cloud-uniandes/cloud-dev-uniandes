"""
Plan B: Pruebas de capacidad de Worker (videos procesados/minuto)
Mide throughput de procesamiento de videos con diferentes tamaños y concurrencia.
"""
import os
import random
import time
import io
import hashlib
from locust import HttpUser, task, between, events
from PIL import Image
import json

# Configuración
API_BASE_URL = os.getenv("API_BASE_URL", "http://anb-api-alb-556459051.us-east-1.elb.amazonaws.com")
TEST_USERNAME = os.getenv("TEST_USERNAME", "worker_test")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "WorkerTest123!")

# Configuración de tamaño de video para la prueba
VIDEO_SIZE_MB = int(os.getenv("VIDEO_SIZE_MB", "50"))  # 50 o 100 MB
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "1"))  # 1, 2, o 4

# Métricas globales para throughput del worker
videos_queued = 0
videos_completed = 0
videos_failed = 0
test_start_time = None


class WorkerLoadUser(HttpUser):
    """
    Usuario que simula carga de videos para medir capacidad del worker.
    Se enfoca en saturar la cola de procesamiento y medir throughput.
    """
    
    wait_time = between(1, 3)  # Tiempo entre uploads
    host = API_BASE_URL
    
    def on_start(self):
        """Setup inicial: crear usuario y login"""
        global test_start_time
        if test_start_time is None:
            test_start_time = time.time()
        
        # Crear usuario único
        username = f"{TEST_USERNAME}_{random.randint(1000, 9999)}"
        email = f"{username}@workertest.com"
        
        # Signup
        signup_data = {
            "first_name": username,
            "last_name": "Test",
            "email": email,
            "password1": TEST_PASSWORD,
            "password2": TEST_PASSWORD,
            "city": "Bogota",
            "country": "Colombia"
        }
        
        with self.client.post(
            "/api/auth/signup",
            json=signup_data,
            name="/auth/signup",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 400]:
                response.success()
            else:
                response.failure(f"Signup failed: {response.status_code}")
        
        # Login
        login_data = {
            "email": email,
            "password": TEST_PASSWORD
        }
        
        with self.client.post(
            "/api/auth/login",
            json=login_data,
            name="/auth/login",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                self.username = username
                response.success()
            else:
                self.token = None
                response.failure(f"Login failed: {response.status_code}")
    
    def generate_video_file(self, size_mb: int) -> io.BytesIO:
        """
        Genera archivo de video dummy del tamaño especificado.
        Simula estructura MP4 básica para pasar validaciones.
        """
        # Crear imagen base
        img = Image.new('RGB', (1280, 720), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        # Calcular tamaño objetivo
        size_bytes = size_mb * 1024 * 1024
        content = buffer.read()
        
        # Rellenar hasta tamaño objetivo
        full_content = content * (size_bytes // len(content) + 1)
        full_content = full_content[:size_bytes]
        
        return io.BytesIO(full_content)
    
    @task(1)
    def upload_video_for_processing(self):
        """
        Upload de video para procesamiento.
        Métricas: tiempo de queue, estado de procesamiento.
        """
        global videos_queued, videos_completed, videos_failed
        
        if not self.token:
            return
        
        # Generar video del tamaño configurado
        video_file = self.generate_video_file(size_mb=VIDEO_SIZE_MB)
        video_hash = hashlib.md5(video_file.getvalue()).hexdigest()[:8]
        
        files = {
            'video_file': (f'worker_test_{video_hash}.mp4', video_file, 'video/mp4')
        }
        
        data = {
            'title': f'Worker Test {VIDEO_SIZE_MB}MB - {video_hash}'
        }
        
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        upload_start = time.time()
        
        with self.client.post(
            "/api/videos/upload",
            files=files,
            data=data,
            headers=headers,
            timeout=120,
            catch_response=True,
            name=f"/videos/upload_{VIDEO_SIZE_MB}MB"
        ) as response:
            upload_time = time.time() - upload_start
            
            if response.status_code in [200, 201, 202]:
                response.success()
                videos_queued += 1
                
                # Extraer task_id o video_id de la respuesta
                try:
                    response_data = response.json()
                    video_id = response_data.get('id') or response_data.get('video_id')
                    task_id = response_data.get('task_id')
                    
                    print(f"✅ Video encolado: {video_hash} | Size: {VIDEO_SIZE_MB}MB | Upload time: {upload_time:.2f}s | Video ID: {video_id}")
                    
                    # Registrar métrica de encolamiento
                    events.request.fire(
                        request_type="VIDEO_QUEUED",
                        name=f"queue_video_{VIDEO_SIZE_MB}MB",
                        response_time=upload_time * 1000,
                        response_length=VIDEO_SIZE_MB * 1024 * 1024,
                        exception=None,
                        context={"video_id": video_id, "task_id": task_id}
                    )
                    
                    # Monitorear estado de procesamiento (opcional, en background)
                    if video_id:
                        self.check_processing_status(video_id, video_hash)
                        
                except Exception as e:
                    print(f"⚠️  Error extrayendo video_id: {e}")
                    
            else:
                response.failure(f"Upload failed: {response.status_code}")
                videos_failed += 1
                print(f"❌ Upload falló: {response.status_code} - {response.text[:100]}")
    
    def check_processing_status(self, video_id: int, video_hash: str, max_checks: int = 5):
        """
        Verifica el estado de procesamiento del video.
        Se ejecuta de forma no bloqueante.
        """
        global videos_completed, videos_failed
        
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        check_start = time.time()
        checks_done = 0
        
        while checks_done < max_checks:
            time.sleep(5)  # Esperar 5 segundos entre checks
            checks_done += 1
            
            with self.client.get(
                f"/api/videos/{video_id}",
                headers=headers,
                catch_response=True,
                name=f"/videos/status_check"
            ) as response:
                if response.status_code == 200:
                    video_data = response.json()
                    status = video_data.get('status', 'unknown')
                    
                    if status == 'completed':
                        processing_time = time.time() - check_start
                        videos_completed += 1
                        
                        print(f"✅ Video procesado: {video_hash} | Time: {processing_time:.2f}s | Status: {status}")
                        
                        # Registrar métrica de procesamiento completo
                        events.request.fire(
                            request_type="VIDEO_PROCESSED",
                            name=f"process_video_{VIDEO_SIZE_MB}MB",
                            response_time=processing_time * 1000,
                            response_length=0,
                            exception=None,
                            context={"video_id": video_id, "status": status}
                        )
                        
                        response.success()
                        return
                        
                    elif status == 'failed':
                        videos_failed += 1
                        print(f"❌ Video falló: {video_hash} | Status: {status}")
                        response.failure(f"Processing failed: {status}")
                        return
                        
                    elif status == 'processing':
                        print(f"⏳ Video procesando: {video_hash} | Check {checks_done}/{max_checks}")
                        response.success()
                        
                else:
                    response.failure(f"Status check failed: {response.status_code}")
                    return
        
        print(f"⚠️  Timeout verificando video: {video_hash} (max checks alcanzado)")


# Eventos de Locust para métricas agregadas
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Inicio de prueba"""
    global test_start_time, videos_queued, videos_completed, videos_failed
    
    test_start_time = time.time()
    videos_queued = 0
    videos_completed = 0
    videos_failed = 0
    
    print(f"\n{'='*80}")
    print(f"🚀 PLAN B: Pruebas de Capacidad Worker")
    print(f"{'='*80}")
    print(f"Target: {API_BASE_URL}")
    print(f"Video Size: {VIDEO_SIZE_MB} MB")
    print(f"Worker Concurrency: {WORKER_CONCURRENCY}")
    print(f"Test Users: {environment.parsed_options.num_users}")
    print(f"Spawn Rate: {environment.parsed_options.spawn_rate}")
    print(f"Run Time: {environment.parsed_options.run_time}")
    print(f"{'='*80}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Resultados finales con métricas de worker"""
    global test_start_time, videos_queued, videos_completed, videos_failed
    
    stats = environment.stats.total
    test_duration_min = (time.time() - test_start_time) / 60
    
    # Calcular throughput del worker
    throughput_per_min = videos_completed / test_duration_min if test_duration_min > 0 else 0
    completion_rate = (videos_completed / videos_queued * 100) if videos_queued > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"✅ RESULTADOS FINALES - PLAN B (Worker Capacity)")
    print(f"{'='*80}")
    print(f"\n📊 MÉTRICAS DE WORKER:")
    print(f"  Videos encolados:        {videos_queued}")
    print(f"  Videos completados:      {videos_completed}")
    print(f"  Videos fallidos:         {videos_failed}")
    print(f"  Tasa de completitud:     {completion_rate:.2f}%")
    print(f"  Throughput:              {throughput_per_min:.2f} videos/min")
    print(f"  Duración total:          {test_duration_min:.2f} minutos")
    print(f"\n📊 MÉTRICAS DE API:")
    print(f"  Total requests:          {stats.num_requests}")
    print(f"  Total failures:          {stats.num_failures}")
    print(f"  Tasa de fallo:           {stats.fail_ratio:.2%}")
    print(f"  RPS promedio:            {stats.total_rps:.2f}")
    print(f"  Latencia p95:            {stats.get_response_time_percentile(0.95):.0f} ms")
    print(f"  Latencia promedio:       {stats.avg_response_time:.0f} ms")
    print(f"{'='*80}\n")
    
    # Breakdown por endpoint
    print("\n📊 BREAKDOWN POR OPERACIÓN:")
    print(f"{'='*80}")
    
    for name, stats_entry in environment.stats.entries.items():
        if stats_entry.num_requests > 0:
            print(f"\n{name[1]}:")
            print(f"  Requests:     {stats_entry.num_requests}")
            print(f"  Failures:     {stats_entry.num_failures} ({stats_entry.fail_ratio:.2%})")
            print(f"  RPS promedio: {stats_entry.total_rps:.2f}")
            print(f"  Latencia avg: {stats_entry.avg_response_time:.0f} ms")
    
    print(f"\n{'='*80}\n")
    
    # Evaluación de capacidad
    print(f"\n🎯 EVALUACIÓN DE CAPACIDAD:")
    print(f"{'='*80}")
    print(f"Configuración: {VIDEO_SIZE_MB}MB x {WORKER_CONCURRENCY} worker(s)")
    print(f"Throughput observado: {throughput_per_min:.2f} videos/min")
    
    if completion_rate >= 95:
        print(f"✅ CAPACIDAD ADECUADA: Tasa de completitud {completion_rate:.2f}% ≥ 95%")
    else:
        print(f"⚠️  CAPACIDAD INSUFICIENTE: Tasa de completitud {completion_rate:.2f}% < 95%")
        print(f"   Recomendación: Aumentar concurrencia de workers")
    
    print(f"{'='*80}\n")