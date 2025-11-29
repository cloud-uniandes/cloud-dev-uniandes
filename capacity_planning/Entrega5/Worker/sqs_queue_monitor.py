"""
Monitor de cola SQS para observar throughput del worker en tiempo real.
"""
import boto3
import time
import json
from datetime import datetime
from pathlib import Path


class SQSQueueMonitor:
    def __init__(self, queue_url: str, region: str = 'us-east-1'):
        """Inicializa monitor de SQS"""
        self.sqs = boto3.client('sqs', region_name=region)
        self.ecs = boto3.client('ecs', region_name=region)
        self.queue_url = queue_url
        self.queue_name = queue_url.split('/')[-1]
        
        print(f"✅ Monitor conectado a: {self.queue_name}")
    
    def get_queue_stats(self):
        """Obtiene estadísticas de SQS"""
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
            'timestamp': datetime.now().isoformat(),
            'messages': int(attrs.get('ApproximateNumberOfMessages', 0)),
            'in_flight': int(attrs.get('ApproximateNumberOfMessagesNotVisible', 0)),
            'delayed': int(attrs.get('ApproximateNumberOfMessagesDelayed', 0))
        }
    
    def get_ecs_tasks_count(self, cluster_name: str, service_name: str):
        """Obtiene número de tasks ECS ejecutándose"""
        try:
            response = self.ecs.describe_services(
                cluster=cluster_name,
                services=[service_name]
            )
            
            if response['services']:
                service = response['services'][0]
                return {
                    'running': service.get('runningCount', 0),
                    'desired': service.get('desiredCount', 0),
                    'pending': service.get('pendingCount', 0)
                }
        except Exception as e:
            print(f"⚠️  No se pudo obtener info de ECS: {e}")
        
        return {'running': 0, 'desired': 0, 'pending': 0}
    
    def monitor(self, duration_seconds=300, interval_seconds=5,
                ecs_cluster=None, ecs_service=None):
        """
        Monitorea SQS durante X segundos.
        """
        print(f"\n{'='*100}")
        print(f"📊 MONITOREANDO COLA SQS")
        print(f"{'='*100}")
        print(f"   Duración: {duration_seconds}s ({duration_seconds/60:.1f} min)")
        print(f"   Intervalo: {interval_seconds}s")
        print(f"   Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if ecs_cluster and ecs_service:
            print(f"   ECS Cluster: {ecs_cluster}")
            print(f"   ECS Service: {ecs_service}")
        
        print(f"\n{'-'*100}")
        print(f"{'Tiempo':<12} {'Mensajes':<12} {'En Vuelo':<12} {'Workers':<10} {'Δ Msgs':<10} {'Throughput':<15}")
        print(f"{'':<12} {'':<12} {'':<12} {'':<10} {'':<10} {'(videos/min)':<15}")
        print(f"{'-'*100}")
        
        samples = []
        start_time = time.time()
        prev_messages = None
        prev_in_flight = None
        
        while time.time() - start_time < duration_seconds:
            stats = self.get_queue_stats()
            elapsed = time.time() - start_time
            
            # Info de ECS
            workers = 0
            if ecs_cluster and ecs_service:
                ecs_info = self.get_ecs_tasks_count(ecs_cluster, ecs_service)
                workers = ecs_info['running']
            
            # Calcular delta y throughput
            delta = 0
            throughput = 0
            
            if prev_messages is not None:
                # Delta negativo = mensajes procesados
                delta = stats['messages'] - prev_messages
                
                # Si disminuyó la cola, calcular throughput
                if delta < 0:
                    throughput = abs(delta) * (60 / interval_seconds)
            
            prev_messages = stats['messages']
            prev_in_flight = stats['in_flight']
            
            # Imprimir fila
            print(f"{elapsed:>10.1f}s  {stats['messages']:>10}  {stats['in_flight']:>10}  "
                  f"{workers:>8}  {delta:>8}  {throughput:>13.2f}")
            
            samples.append({
                **stats,
                'elapsed': elapsed,
                'delta': delta,
                'throughput': throughput,
                'workers': workers
            })
            
            time.sleep(interval_seconds)
        
        # Resumen
        print(f"\n{'='*100}")
        print(f"📈 RESUMEN DE PRUEBA")
        print(f"{'='*100}")
        
        if len(samples) > 1:
            total_processed = abs(sum(s['delta'] for s in samples if s['delta'] < 0))
            duration_min = duration_seconds / 60
            avg_throughput = total_processed / duration_min if duration_min > 0 else 0
            
            print(f"   Videos procesados: {total_processed}")
            print(f"   Throughput promedio: {avg_throughput:.2f} videos/min")
            print(f"   Mensajes en cola (final): {samples[-1]['messages']}")
            print(f"   Mensajes en vuelo (final): {samples[-1]['in_flight']}")
            print(f"   Workers activos (final): {samples[-1]['workers']}")
            print(f"   Duración real: {samples[-1]['elapsed']:.1f}s")
            
            # Evaluar estabilidad
            queue_growth = samples[-1]['messages'] - samples[0]['messages']
            
            if queue_growth > 10:
                print(f"\n   ⚠️  SATURACIÓN: Cola creció +{queue_growth} mensajes")
                print(f"       El worker no procesa suficientemente rápido")
            elif queue_growth < -10:
                print(f"\n   ✅ ESTABLE: Cola decreció {queue_growth} mensajes")
                print(f"       Capacidad sobrada del worker")
            else:
                print(f"\n   ✅ EQUILIBRADO: Cola estable ({queue_growth:+d} mensajes)")
                print(f"       Worker procesa a la velocidad adecuada")
        
        return samples
    
    def save_results(self, samples: list, test_name: str = None):
        """Guarda resultados en JSON"""
        Path('results').mkdir(exist_ok=True)
        
        if test_name:
            output_file = f'results/{test_name}.json'
        else:
            output_file = f'results/sqs_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        summary = {
            'total_processed': abs(sum(s['delta'] for s in samples if s['delta'] < 0)),
            'duration_minutes': samples[-1]['elapsed'] / 60 if samples else 0,
            'avg_throughput': 0
        }
        
        if summary['duration_minutes'] > 0:
            summary['avg_throughput'] = summary['total_processed'] / summary['duration_minutes']
        
        with open(output_file, 'w') as f:
            json.dump({
                'queue_name': self.queue_name,
                'test_name': test_name,
                'samples': samples,
                'summary': summary
            }, f, indent=2)
        
        print(f"\n💾 Resultados guardados: {output_file}")
        return output_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor de cola SQS')
    parser.add_argument('--queue-url', required=True)
    parser.add_argument('--duration', type=int, default=300)
    parser.add_argument('--interval', type=int, default=5)
    parser.add_argument('--ecs-cluster', help='Cluster ECS')
    parser.add_argument('--ecs-service', help='Servicio worker ECS')
    parser.add_argument('--test-name', help='Nombre del test')
    parser.add_argument('--region', default='us-east-1')
    
    args = parser.parse_args()
    
    monitor = SQSQueueMonitor(queue_url=args.queue_url, region=args.region)
    
    samples = monitor.monitor(
        duration_seconds=args.duration,
        interval_seconds=args.interval,
        ecs_cluster=args.ecs_cluster,
        ecs_service=args.ecs_service
    )
    
    output_file = monitor.save_results(samples, test_name=args.test_name)
    
    print(f"\n🔍 Para analizar:")
    print(f"   python analyze_results.py {output_file}")


if __name__ == '__main__':
    main()