"""
Plan A: Pruebas de capacidad de la capa Web 
"""
import os
import random
import io
from locust import HttpUser, task, between, events
from PIL import Image
import time

# Configuración desde variables de entorno
API_BASE_URL = os.getenv("API_BASE_URL", "http://anb-api-alb-556459051.us-east-1.elb.amazonaws.com")
TEST_USERNAME = os.getenv("TEST_USERNAME", "loadtest")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "LoadTest123!")


class VideoUploadUser(HttpUser):
    """
    Usuario que simula subida de videos a la API real.
    """
    
    wait_time = between(2, 5)  # Espera entre requests
    host = API_BASE_URL
    
    def on_start(self):
        """Login al iniciar cada usuario"""
        # Crear usuario único 
        username = f"{TEST_USERNAME}_{random.randint(100000, 999999)}"
        email = f"{username}@loadtest.com"
        
        # Signup
        with self.client.post(
            "/api/auth/signup",
            json={
                "first_name": username,
                "last_name": username,
                "email": email,
                "password1": TEST_PASSWORD,
                "password2": TEST_PASSWORD,
                "city": "string",
                "country": "string"
            },
            name="/auth/signup",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                print(f"Usuario creado: {username}")
            elif response.status_code == 400:
                print(f"Usuario ya existe: {username}")
            else:
                print(f"Error signup: {response.status_code} - {response.text}")
        
        # Login para obtener token
        with self.client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": TEST_PASSWORD
            },
            name="/auth/login",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                print(f"Login exitoso: {username[:20]}...")
                response.success()
            else:
                # Si falla, usar usuario por defecto
                self.token = None
                print(f"Login falló: {response.status_code} - {response.text}")
                response.failure(f"Login failed: {response.status_code}")
    
    def generate_dummy_video(self, size_mb: int = 1) -> io.BytesIO:
        """
        Genera un archivo dummy MP4.
        """
        # Generar imagen simple
        img = Image.new('RGB', (640, 480), color=(73, 109, 137))
        
        # Guardar como bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        # Rellenar hasta el tamaño deseado
        size_bytes = size_mb * 1024 * 1024
        content = buffer.read()
        
        # Repetir contenido hasta alcanzar tamaño
        full_content = content * (size_bytes // len(content) + 1)
        full_content = full_content[:size_bytes]
        
        return io.BytesIO(full_content)
    
    @task(1)  
    def upload_video(self):
        """
        Simula subida de video.
        Mide tiempo hasta recibir 202 Accepted.
        """
        if not self.token:
            return  # Skip si no hay token
        
        # Generar archivo dummy
        video_file = self.generate_dummy_video(size_mb=1)
        
        files = {
            'video_file': ('test_video.mp4', video_file, 'video/mp4')
        }
        
        data = {
            'title': f'Load Test {random.randint(10000, 99999)}'
        }
        
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        # Medir solo hasta recibir 202
        start_time = time.time()
        
        with self.client.post(
            "/api/videos/upload",
            files=files,
            data=data,
            headers=headers,
            timeout=120,  # 60 segundos máximo para uploads
            catch_response=True,
            name="/videos/upload"
        ) as response:
            elapsed = time.time() - start_time
            
            if response.status_code == 201:
                response.success()
                print(f"✅ Upload exitoso en {elapsed:.2f}s")
                # Registrar métrica personalizada
                events.request.fire(
                    request_type="UPLOAD_SUCCESS",
                    name="upload_latency",
                    response_time=elapsed * 1000,
                    response_length=len(video_file.getvalue()),
                    exception=None,
                    context={}
                )
            elif response.status_code == 401:
                response.failure("Unauthorized - Token expired")
                print(f"❌ Upload falló: 401 Unauthorized")
            elif response.status_code == 413:
                response.failure("File too large")
                print(f"❌ Upload falló: 413 File too large")
            elif response.status_code == 422:
                response.failure("Validation error")
                print(f"❌ Upload falló: 422 Validation - {response.text}")
            else:
                response.failure(f"Upload failed: {response.status_code}")
                print(f"❌ Upload falló: {response.status_code} - {response.text[:100]}")
    
    @task(1)  # Peso 1 - health check
    def health_check(self):
        """Verifica salud del API"""
        with self.client.get(
            "/health",
            name="/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    @task(1)
    def get_videos(self):
        if not self.token:
            return
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        with self.client.get(
            "/api/videos",
            name="/api/videos",
            catch_response=True,
            headers=headers
        ) as response:
            if response.status_code == 200:
                response.success()
                videos = response.json()
                if videos:
                    self.last_user_video = videos[0]["video_id"]
                else:
                    self.last_user_video = None
                response.success()
            else:
                response.failure(f"Get videos failes: {response.status_code}")
    
    @task(1)
    def get_video_by_id(self):
        """Consulta un video específico del usuario."""
        if not self.token:
            return

        # Verificar si existe un video previo
        if not hasattr(self, "last_user_video") or not self.last_user_video:
            return

        headers = {
            'Authorization': f'Bearer {self.token}'
        }

        video_id = self.last_user_video

        with self.client.get(
            f"/api/videos/{video_id}",
            name="/api/videos/video_id",
            catch_response=True,
            headers=headers
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get video by id failed: {response.status_code}")
                print(f"❌ Get video by id falló - {response.text}")

    @task(1)
    def publish_user_video(self):
        if not self.token or not hasattr(self, "last_user_video"):
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        video_id = self.last_user_video

        with self.client.put(
            f"/api/videos/{video_id}/publish",
            name="/api/videos/publish",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 400]:
                response.success()
            else:
                response.failure(f"Publish failed: {response.status_code}")


    @task(1)
    def list_public_videos(self):

        with self.client.get(
            "/api/public/videos",
            name="/api/public/videos",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                self.last_public_videos = response.json()
                response.success()
            else:
                response.failure(f"Failed list videos {response.status_code}")
    @task(1)
    def vote_video(self):

        if not self.token:
            return
        
        if not hasattr(self, "last_public_videos") or not self.last_public_videos:
            return

        video = random.choice(self.last_public_videos)
        video_id = video["video_id"]

        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        with self.client.post(
            f"/api/public/videos/{video_id}/vote",
            name="/api/public/videos/{video_id}/vote",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400:
                response.success()  # ya votó 
            elif response.status_code == 404:
                response.success()  # video no existe 
            else:
                response.failure(f"Vote failed {response.status_code}")

    @task(1)
    def get_rankings(self):
  
        with self.client.get(
            "/api/public/rankings",
            name="/rankings",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Rankings failed {response.status_code}")




# Listeners para métricas personalizadas
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta al inicio de la prueba"""
    print(f"\n{'='*80}")
    print(f"PLAN A: Pruebas de Capacidad Web")
    print(f"{'='*80}")
    print(f"Target: {API_BASE_URL}")
    print(f"Test: {environment.parsed_options.num_users} usuarios")
    print(f"Spawn rate: {environment.parsed_options.spawn_rate} usuarios/seg")
    print(f"Run time: {environment.parsed_options.run_time}")
    print(f"{'='*80}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta al finalizar la prueba"""
    stats = environment.stats.total
    
    print(f"\n{'='*80}")
    print(f"RESULTADOS FINALES - PLAN A")
    print(f"{'='*80}")
    print(f"Total requests:        {stats.num_requests}")
    print(f"Total failures:        {stats.num_failures}")
    print(f"Tasa de fallo:         {stats.fail_ratio:.2%}")
    print(f"RPS promedio:          {stats.total_rps:.2f}")
    print(f"{'='*80}\n")
    
    # Verificar cumplimiento de SLOs
    p95_latency = stats.get_response_time_percentile(0.95)
    fail_ratio = stats.fail_ratio
    
    slo_met = p95_latency <= 1000 and fail_ratio <= 0.05
    
    if slo_met:
        print("SLOs CUMPLIDOS")
        print(f"   ✓ p95 latency: {p95_latency:.0f} ms ≤ 1000 ms")
        print(f"   ✓ Error rate: {fail_ratio:.2%} ≤ 5%")
    else:
        print("SLOs NO CUMPLIDOS")
        if p95_latency > 1000:
            print(f"   ✗ p95 latency: {p95_latency:.0f} ms > 1000 ms")
        if fail_ratio > 0.05:
            print(f"   ✗ Error rate: {fail_ratio:.2%} > 5%")
    
    print(f"{'='*80}\n")
    
    # Mostrar breakdown por endpoint
    print("\nBREAKDOWN POR ENDPOINT:")
    print(f"{'='*80}")
    
    for name, stats_entry in environment.stats.entries.items():
        if stats_entry.num_requests > 0:
            print(f"\n{name[1]}:")  # name es tuple (method, path)
            print(f"  Requests:     {stats_entry.num_requests}")
            print(f"  Failures:     {stats_entry.num_failures} ({stats_entry.fail_ratio:.2%})")
            print(f"  RPS promedio: {stats_entry.total_rps:.2f}")
            print(f"  Latencia p95: {stats_entry.get_response_time_percentile(0.95):.0f} ms")
            print(f"  Latencia avg: {stats_entry.avg_response_time:.0f} ms")
    
    print(f"\n{'='*80}\n")