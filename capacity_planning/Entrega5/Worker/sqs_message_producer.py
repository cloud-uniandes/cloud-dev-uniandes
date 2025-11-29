"""
Productor de mensajes adaptado para cola SQS STANDARD.
"""
import boto3
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
import argparse


class SQSWorkerTester:
    def __init__(self, queue_url: str, region: str = 'us-east-1'):
        """Inicializa cliente SQS"""
        self.sqs = boto3.client('sqs', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.queue_url = queue_url
        self.queue_name = queue_url.split('/')[-1]
        
        # Detectar si es FIFO o Standard
        self.is_fifo = self.queue_name.endswith('.fifo')
        
        print(f"✅ Conectado a SQS: {self.queue_name}")
        print(f"   Tipo: {'FIFO' if self.is_fifo else 'Standard'}")
    
    def upload_test_video_to_s3(self, local_path: str, bucket: str, s3_key: str):
        """Sube video de prueba a S3"""
        file_size_mb = Path(local_path).stat().st_size / (1024 * 1024)
        print(f"⬆️  Subiendo {Path(local_path).name} ({file_size_mb:.1f} MB) a s3://{bucket}/{s3_key}")
        
        try:
            self.s3.upload_file(local_path, bucket, s3_key)
            return f"s3://{bucket}/{s3_key}"
        except Exception as e:
            print(f"   ❌ Error subiendo a S3: {e}")
            raise
    
    def send_task(self, video_id: int, s3_key: str, s3_bucket: str, user_id: int = 1):
        """
        Envía tarea a SQS (compatible con FIFO y Standard).
        """
        task_id = str(uuid.uuid4())
        
        message_body = {
            'video_id': video_id,
            'user_id': user_id,
            's3_key': s3_key,
            's3_bucket': s3_bucket,
            'task_id': task_id,
            'enqueued_at': datetime.now().isoformat()
        }
        
        # Parámetros base
        params = {
            'QueueUrl': self.queue_url,
            'MessageBody': json.dumps(message_body)
        }
        
        # Si es FIFO, agregar parámetros adicionales
        if self.is_fifo:
            params['MessageGroupId'] = f"user_{user_id}"
            params['MessageDeduplicationId'] = task_id
        
        response = self.sqs.send_message(**params)
        
        return task_id, response['MessageId']
    
    def inject_batch(self, test_videos: dict, num_videos: int, 
                     s3_bucket: str, delay_ms: int = 0):
        """
        Inyecta lote de N videos en SQS.
        """
        print(f"\n{'='*70}")
        print(f"📤 INYECTANDO {num_videos} TAREAS EN SQS")
        print(f"{'='*70}")
        print(f"   Bucket S3: {s3_bucket}")
        print(f"   Delay: {delay_ms}ms entre mensajes")
        print(f"   Tamaños: {', '.join(test_videos.keys())}")
        
        # 1. Subir videos de prueba a S3 (solo una vez)
        s3_videos = {}
        print(f"\n📦 Verificando videos en S3...")
        
        for size, local_path in test_videos.items():
            s3_key = f"test_videos/{Path(local_path).name}"
            
            # Verificar si ya existe
            try:
                self.s3.head_object(Bucket=s3_bucket, Key=s3_key)
                print(f"   ✓ {size}: Ya existe en S3")
            except:
                print(f"   Subiendo {size}...")
                self.upload_test_video_to_s3(local_path, s3_bucket, s3_key)
            
            s3_videos[size] = {'s3_key': s3_key, 'local_path': local_path}
        
        # 2. Encolar mensajes
        print(f"\n📨 Encolando mensajes...")
        
        tasks = []
        start_time = time.time()
        video_sizes = list(s3_videos.keys())
        
        for i in range(1, num_videos + 1):
            # Alternar entre tamaños
            size = video_sizes[i % len(video_sizes)]
            s3_key = s3_videos[size]['s3_key']
            
            try:
                task_id, message_id = self.send_task(
                    video_id=2000 + i,  # IDs únicos empezando en 2000
                    s3_key=s3_key,
                    s3_bucket=s3_bucket,
                    user_id=(i % 10) + 1
                )
                
                tasks.append({
                    'task_id': task_id,
                    'message_id': message_id,
                    'video_id': 2000 + i,
                    'size': size,
                    'enqueued_at': datetime.now().isoformat(),
                    's3_key': s3_key
                })
                
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)
                
                if i % 10 == 0:
                    print(f"   ✓ {i}/{num_videos} tareas encoladas...")
            
            except Exception as e:
                print(f"   ❌ Error encolando mensaje {i}: {e}")
                continue
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"✅ LOTE COMPLETADO")
        print(f"{'='*70}")
        print(f"   Tiempo: {elapsed:.2f}s")
        print(f"   Tareas exitosas: {len(tasks)}/{num_videos}")
        print(f"   Tasa de inyección: {len(tasks)/elapsed:.2f} tareas/s")
        
        # Guardar log
        Path('results').mkdir(exist_ok=True)
        log_file = f'results/injected_tasks_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(log_file, 'w') as f:
            json.dump(tasks, f, indent=2)
        
        print(f"   📄 Log guardado: {log_file}")
        
        return tasks
    
    def get_queue_stats(self):
        """Obtiene estadísticas actuales de la cola"""
        response = self.sqs.get_queue_attributes(
            QueueUrl=self.queue_url,
            AttributeNames=[
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible',
                'ApproximateNumberOfMessagesDelayed'
            ]
        )
        
        attrs = response['Attributes']
        return {
            'messages': int(attrs.get('ApproximateNumberOfMessages', 0)),
            'in_flight': int(attrs.get('ApproximateNumberOfMessagesNotVisible', 0)),
            'delayed': int(attrs.get('ApproximateNumberOfMessagesDelayed', 0))
        }


def create_test_videos():
    """Genera videos de prueba con FFmpeg"""
    import subprocess
    
    output_dir = Path('./test_videos')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sizes = {
        '50MB': {'duration': 60, 'bitrate': '7000k'},
        '100MB': {'duration': 120, 'bitrate': '7000k'}
    }
    
    print("\n🎬 Generando videos de prueba con FFmpeg...")
    print("   (Esto puede tardar 2-3 minutos...)")
    
    test_files = {}
    
    for size_name, params in sizes.items():
        output_file = output_dir / f'test_video_{size_name}.mp4'
        
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"   ✓ {size_name}: {output_file} ({size_mb:.1f} MB) - Ya existe")
            test_files[size_name] = str(output_file)
            continue
        
        print(f"   Generando {size_name}...")
        
        try:
            subprocess.run([
                'ffmpeg', '-f', 'lavfi', '-i',
                f'testsrc=duration={params["duration"]}:size=1920x1080:rate=30',
                '-f', 'lavfi', '-i', f'sine=frequency=1000:duration={params["duration"]}',
                '-c:v', 'libx264', '-b:v', params['bitrate'],
                '-c:a', 'aac', '-b:a', '128k',
                '-pix_fmt', 'yuv420p',
                '-y', str(output_file)
            ], check=True, capture_output=True, text=True)
            
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"   ✓ {size_name}: {output_file} ({size_mb:.1f} MB)")
            
            test_files[size_name] = str(output_file)
        
        except FileNotFoundError:
            print(f"\n   ❌ FFmpeg no encontrado.")
            print(f"   Descarga desde: https://ffmpeg.org/download.html")
            print(f"   Windows: https://www.gyan.dev/ffmpeg/builds/")
            return None
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error al generar video: {e.stderr}")
            return None
    
    return test_files


def main():
    parser = argparse.ArgumentParser(description='Pruebas de capacidad Worker en AWS')
    parser.add_argument('--queue-url', 
                       default='https://queue.amazonaws.com/317968594062/message-queue',
                       help='URL de la cola SQS')
    parser.add_argument('--s3-bucket',  # ❌ QUITAR required=True
                       help='Bucket S3 para videos de prueba')
    parser.add_argument('--mode', choices=['saturation', 'sustained', 'generate'],
                       default='sustained', help='Modo de prueba')
    parser.add_argument('--num-videos', type=int, default=20,
                       help='Número de videos a procesar')
    parser.add_argument('--delay-ms', type=int, default=0,
                       help='Delay entre mensajes (ms)')
    parser.add_argument('--region', default='us-east-1')
    
    args = parser.parse_args()
    
    # Generar videos
    if args.mode == 'generate':
        test_files = create_test_videos()
        if test_files:
            print(f"\n✅ Videos de prueba listos en: ./test_videos/")
        return
    
    # ✅ AGREGAR: Validar S3 bucket solo si NO es modo generate
    if not args.s3_bucket:
        print("❌ Error: --s3-bucket es requerido para modos 'saturation' y 'sustained'")
        parser.print_help()
        return
    
    # Generar videos
    if args.mode == 'generate':
        test_files = create_test_videos()
        if test_files:
            print(f"\n✅ Videos de prueba listos en: ./test_videos/")
        return
    
    # Verificar videos de prueba
    test_videos = {}
    for size in ['50MB', '100MB']:
        path = f'./test_videos/test_video_{size}.mp4'
        if not Path(path).exists():
            print(f"❌ Video no encontrado: {path}")
            print("   Ejecuta primero: python sqs_message_producer.py --mode generate")
            return
        test_videos[size] = path
    
    # Conectar y ejecutar
    tester = SQSWorkerTester(queue_url=args.queue_url, region=args.region)
    
    # Mostrar estado inicial
    print(f"\n📊 Estado inicial de la cola:")
    stats = tester.get_queue_stats()
    print(f"   Mensajes: {stats['messages']}")
    print(f"   En vuelo: {stats['in_flight']}")
    
    if stats['messages'] > 0:
        print(f"\n⚠️  ADVERTENCIA: La cola ya tiene {stats['messages']} mensajes")
        response = input("   ¿Continuar de todos modos? (s/n): ")
        if response.lower() != 's':
            print("   Operación cancelada")
            return
    
    if args.mode == 'saturation':
        print(f"\n🔥 MODO SATURACIÓN")
        tester.inject_batch(test_videos, args.num_videos, args.s3_bucket, args.delay_ms)
    
    elif args.mode == 'sustained':
        print(f"\n⚖️  MODO SOSTENIDO")
        tester.inject_batch(test_videos, args.num_videos, args.s3_bucket, args.delay_ms)


if __name__ == '__main__':
    main()