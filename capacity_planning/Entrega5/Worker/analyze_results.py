"""
Analiza resultados de pruebas de capacidad y genera gráficas.
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse


def analyze_test_results(stats_file: str):
    """Analiza resultados y genera gráficas"""
    
    with open(stats_file, 'r') as f:
        data = json.load(f)
    
    samples = data['samples']
    summary = data['summary']
    test_name = data.get('test_name', 'Unknown')
    
    df = pd.DataFrame(samples)
    
    # Información del test
    print(f"\n{'='*80}")
    print(f"📊 ANÁLISIS DE RESULTADOS")
    print(f"{'='*80}")
    print(f"Test: {test_name}")
    print(f"Archivo: {stats_file}")
    print(f"Duración: {summary['duration_minutes']:.2f} minutos")
    print(f"Videos procesados: {summary['total_processed']}")
    print(f"Throughput promedio: {summary['avg_throughput']:.2f} videos/min")
    print(f"Mensajes finales: {df['messages'].iloc[-1]}")
    print(f"Workers finales: {df['workers'].iloc[-1]}")
    
    # Evaluar estabilidad
    queue_growth = df['messages'].iloc[-1] - df['messages'].iloc[0]
    if queue_growth > 10:
        status = "⚠️  SATURADA"
        recommendation = "Aumentar workers o concurrencia"
    elif queue_growth < -10:
        status = "✅ SOBRECAPACIDAD"
        recommendation = "Reducir workers para ahorrar costos"
    else:
        status = "✅ ESTABLE"
        recommendation = "Configuración óptima"
    
    print(f"\nEstado: {status}")
    print(f"Crecimiento de cola: {queue_growth:+d} mensajes")
    print(f"Recomendación: {recommendation}")
    
    # Estadísticas adicionales
    print(f"\n{'='*80}")
    print(f"📈 ESTADÍSTICAS DETALLADAS")
    print(f"{'='*80}")
    print(f"Throughput máximo: {df['throughput'].max():.2f} videos/min")
    print(f"Throughput promedio: {df['throughput'].mean():.2f} videos/min")
    print(f"Mensajes máximos en cola: {df['messages'].max()}")
    print(f"Workers promedio: {df['workers'].mean():.1f}")
    
    # Crear gráficas
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Gráfica 1: Mensajes en cola
    axes[0].plot(df['elapsed']/60, df['messages'], 'b-', linewidth=2, label='Mensajes en cola')
    axes[0].plot(df['elapsed']/60, df['in_flight'], 'orange', linewidth=2, label='En procesamiento')
    axes[0].set_xlabel('Tiempo (minutos)', fontsize=11)
    axes[0].set_ylabel('Cantidad de Mensajes', fontsize=11)
    axes[0].set_title(f'Profundidad de Cola - {test_name}', fontsize=13, fontweight='bold')
    axes[0].legend(loc='best')
    axes[0].grid(True, alpha=0.3)
    
    # Gráfica 2: Throughput
    axes[1].plot(df['elapsed']/60, df['throughput'], 'g-', linewidth=2)
    axes[1].axhline(y=summary['avg_throughput'], color='r', linestyle='--',
                   label=f'Promedio: {summary["avg_throughput"]:.2f} videos/min', linewidth=2)
    axes[1].set_xlabel('Tiempo (minutos)', fontsize=11)
    axes[1].set_ylabel('Throughput (videos/min)', fontsize=11)
    axes[1].set_title('Throughput del Worker', fontsize=13, fontweight='bold')
    axes[1].legend(loc='best')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_ylim(bottom=0)
    
    
    plt.tight_layout()
    
    # Guardar gráfica
    output_img = stats_file.replace('.json', '.png')
    plt.savefig(output_img, dpi=300, bbox_inches='tight')
    print(f"\n📈 Gráficas guardadas: {output_img}")
    
    plt.show()
    
    return summary


def generate_comparison_table(results_dir='results'):
    """Genera tabla comparativa de todos los tests"""
    
    results_path = Path(results_dir)
    json_files = list(results_path.glob('test_*.json'))
    
    if not json_files:
        print("No se encontraron resultados de tests")
        return
    
    print(f"\n{'='*120}")
    print(f"📊 TABLA COMPARATIVA DE TODAS LAS PRUEBAS")
    print(f"{'='*120}")
    
    # Encabezados
    print(f"{'Test':<40} {'Videos/min':<15} {'Procesados':<15} {'Cola Final':<15} {'Estado':<15}")
    print(f"{'-'*120}")
    
    results = []
    
    for json_file in sorted(json_files):
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        test_name = data.get('test_name', json_file.stem)
        summary = data['summary']
        samples = data['samples']
        
        queue_growth = samples[-1]['messages'] - samples[0]['messages']
        
        if queue_growth > 10:
            status = "⚠️  SATURADA"
        elif queue_growth < -10:
            status = "✅ SOBRECAP"
        else:
            status = "✅ ESTABLE"
        
        print(f"{test_name:<40} {summary['avg_throughput']:>13.2f}  {summary['total_processed']:>13}  "
              f"{samples[-1]['messages']:>13}  {status:<15}")
        
        results.append({
            'test': test_name,
            'throughput': summary['avg_throughput'],
            'processed': summary['total_processed'],
            'queue_final': samples[-1]['messages'],
            'status': status
        })
    
    print(f"{'-'*120}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Analizar resultados de pruebas')
    parser.add_argument('stats_file', nargs='?', help='Archivo JSON con estadísticas')
    parser.add_argument('--compare', action='store_true', help='Comparar todos los tests')
    
    args = parser.parse_args()
    
    if args.compare:
        generate_comparison_table()
    elif args.stats_file:
        analyze_test_results(args.stats_file)
    else:
        print("Uso:")
        print("  python analyze_results.py <archivo.json>")
        print("  python analyze_results.py --compare")


if __name__ == '__main__':
    main()