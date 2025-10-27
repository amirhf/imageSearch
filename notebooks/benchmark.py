"""
ImageSearch Benchmark Script
=============================

Comprehensive benchmarking for local vs cloud caption quality, latency, and cost analysis.

Usage:
    python notebooks/benchmark.py --api-url http://localhost:8000 --sample-size 100
    
Requirements:
    pip install matplotlib seaborn pandas nltk pycocotools
"""

import asyncio
import httpx
import json
import time
import statistics
from pathlib import Path
from typing import List, Dict, Tuple
import argparse

# Optional imports with graceful fallback
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    print("WARNING: matplotlib/seaborn not available. Plotting disabled.")
    PLOTTING_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("WARNING: pandas not available. Some analysis features disabled.")
    PANDAS_AVAILABLE = False

try:
    from nltk.translate.bleu_score import sentence_bleu
    from nltk.translate.meteor_score import meteor_score
    import nltk
    # Download required NLTK data
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        print("Downloading NLTK data...")
        nltk.download('wordnet', quiet=True)
        nltk.download('punkt', quiet=True)
        nltk.download('omw-1.4', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    print("WARNING: NLTK not available. Caption quality metrics disabled.")
    NLTK_AVAILABLE = False


class ImageSearchBenchmark:
    """Benchmark suite for ImageSearch system"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url.rstrip('/')
        self.results = {
            'local_latencies': [],
            'cloud_latencies': [],
            'local_captions': [],
            'cloud_captions': [],
            'ground_truth_captions': [],
            'costs': [],
            'image_ids': [],
            'search_latencies': [],
            'search_recalls': []
        }
    
    async def benchmark_caption_latency(self, image_path: str, num_runs: int = 10) -> Dict:
        """Benchmark caption generation latency"""
        print(f"\n{'='*60}")
        print(f"Benchmarking Caption Latency ({num_runs} runs)")
        print(f"{'='*60}")
        
        latencies = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            for i in range(num_runs):
                start = time.perf_counter()
                
                files = {'file': ('test.jpg', image_data, 'image/jpeg')}
                response = await client.post(f"{self.api_url}/images", files=files)
                response.raise_for_status()
                result = response.json()
                
                end = time.perf_counter()
                latency_ms = (end - start) * 1000
                latencies.append(latency_ms)
                
                print(f"Run {i+1}/{num_runs}: {latency_ms:.2f}ms - {result.get('origin', 'unknown')} - {result.get('caption', '')[:50]}...")
            
            stats = {
                'mean': statistics.mean(latencies),
                'median': statistics.median(latencies),
                'p95': self._percentile(latencies, 95),
                'p99': self._percentile(latencies, 99),
                'min': min(latencies),
                'max': max(latencies),
                'stdev': statistics.stdev(latencies) if len(latencies) > 1 else 0
            }
            
            print(f"\nLatency Statistics:")
            print(f"  Mean:   {stats['mean']:.2f}ms")
            print(f"  Median: {stats['median']:.2f}ms")
            print(f"  P95:    {stats['p95']:.2f}ms")
            print(f"  P99:    {stats['p99']:.2f}ms")
            print(f"  StdDev: {stats['stdev']:.2f}ms")
            
            return stats
    
    async def benchmark_search_latency(self, queries: List[str], k: int = 10) -> Dict:
        """Benchmark search latency and recall"""
        print(f"\n{'='*60}")
        print(f"Benchmarking Search Performance")
        print(f"{'='*60}")
        
        latencies = []
        results_counts = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for query in queries:
                start = time.perf_counter()
                
                response = await client.get(
                    f"{self.api_url}/search",
                    params={"q": query, "k": k}
                )
                response.raise_for_status()
                result = response.json()
                
                end = time.perf_counter()
                latency_ms = (end - start) * 1000
                latencies.append(latency_ms)
                results_counts.append(len(result.get('results', [])))
                
                print(f"Query: '{query[:40]}...' - {latency_ms:.2f}ms - {results_counts[-1]} results")
        
        stats = {
            'mean_latency': statistics.mean(latencies),
            'median_latency': statistics.median(latencies),
            'mean_results': statistics.mean(results_counts) if results_counts else 0
        }
        
        print(f"\nSearch Statistics:")
        print(f"  Mean Latency:   {stats['mean_latency']:.2f}ms")
        print(f"  Median Latency: {stats['median_latency']:.2f}ms")
        print(f"  Avg Results:    {stats['mean_results']:.1f}")
        
        return stats
    
    def calculate_caption_quality(
        self, 
        generated: str, 
        references: List[str]
    ) -> Dict:
        """Calculate BLEU and METEOR scores for caption quality"""
        if not NLTK_AVAILABLE:
            return {'bleu': 0, 'meteor': 0, 'note': 'NLTK not available'}
        
        try:
            # Tokenize
            gen_tokens = generated.lower().split()
            ref_tokens_list = [ref.lower().split() for ref in references]
            
            # BLEU score
            bleu = sentence_bleu(ref_tokens_list, gen_tokens)
            
            # METEOR score (single reference)
            meteor = meteor_score(ref_tokens_list, gen_tokens)
            
            return {
                'bleu': bleu,
                'meteor': meteor
            }
        except Exception as e:
            print(f"Error calculating quality metrics: {e}")
            return {'bleu': 0, 'meteor': 0, 'error': str(e)}
    
    def estimate_cost(
        self, 
        num_images: int, 
        cloud_percentage: float = 0.2,
        tokens_per_image: int = 500,
        cost_per_1m_tokens: float = 0.15
    ) -> Dict:
        """Estimate costs for processing images"""
        print(f"\n{'='*60}")
        print(f"Cost Estimation")
        print(f"{'='*60}")
        
        cloud_images = int(num_images * cloud_percentage)
        local_images = num_images - cloud_images
        
        total_tokens = cloud_images * tokens_per_image
        total_cost = (total_tokens / 1_000_000) * cost_per_1m_tokens
        cost_per_1k = (total_cost / num_images) * 1000
        
        print(f"Scenario: {num_images:,} images, {cloud_percentage*100:.0f}% cloud")
        print(f"  Local images:  {local_images:,} (free)")
        print(f"  Cloud images:  {cloud_images:,}")
        print(f"  Total tokens:  {total_tokens:,}")
        print(f"  Total cost:    ${total_cost:.4f}")
        print(f"  Cost per 1K:   ${cost_per_1k:.4f}")
        
        return {
            'num_images': num_images,
            'cloud_percentage': cloud_percentage,
            'local_images': local_images,
            'cloud_images': cloud_images,
            'total_cost': total_cost,
            'cost_per_1k': cost_per_1k
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower = int(index)
        upper = lower + 1
        weight = index - lower
        
        if upper >= len(sorted_data):
            return sorted_data[-1]
        
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight
    
    def plot_latency_distribution(self, latencies: List[float], title: str = "Latency Distribution"):
        """Plot latency distribution histogram"""
        if not PLOTTING_AVAILABLE:
            print("Plotting not available (matplotlib/seaborn not installed)")
            return
        
        plt.figure(figsize=(10, 6))
        plt.hist(latencies, bins=30, edgecolor='black', alpha=0.7)
        plt.axvline(statistics.mean(latencies), color='red', linestyle='--', 
                   label=f'Mean: {statistics.mean(latencies):.2f}ms')
        plt.axvline(statistics.median(latencies), color='green', linestyle='--',
                   label=f'Median: {statistics.median(latencies):.2f}ms')
        plt.xlabel('Latency (ms)')
        plt.ylabel('Frequency')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('latency_distribution.png', dpi=150)
        print(f"Plot saved to: latency_distribution.png")
        plt.close()
    
    def plot_cost_quality_tradeoff(self, scenarios: List[Dict]):
        """Plot cost vs quality tradeoff"""
        if not PLOTTING_AVAILABLE or not PANDAS_AVAILABLE:
            print("Plotting requires matplotlib, seaborn, and pandas")
            return
        
        df = pd.DataFrame(scenarios)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Cost curve
        ax1.plot(df['cloud_percentage'] * 100, df['cost_per_1k'], 
                marker='o', linewidth=2)
        ax1.set_xlabel('Cloud Usage (%)')
        ax1.set_ylabel('Cost per 1K Images ($)')
        ax1.set_title('Cost vs Cloud Usage')
        ax1.grid(True, alpha=0.3)
        
        # Quality curve (if available)
        if 'quality_score' in df.columns:
            ax2.plot(df['cloud_percentage'] * 100, df['quality_score'],
                    marker='s', linewidth=2, color='green')
            ax2.set_xlabel('Cloud Usage (%)')
            ax2.set_ylabel('Quality Score')
            ax2.set_title('Quality vs Cloud Usage')
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'Quality data not available',
                    ha='center', va='center', transform=ax2.transAxes)
        
        plt.tight_layout()
        plt.savefig('cost_quality_tradeoff.png', dpi=150)
        print(f"Plot saved to: cost_quality_tradeoff.png")
        plt.close()
    
    def generate_report(self, output_file: str = "benchmark_report.json"):
        """Generate comprehensive benchmark report"""
        print(f"\n{'='*60}")
        print(f"Generating Benchmark Report")
        print(f"{'='*60}")
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'api_url': self.api_url,
            'results': self.results,
            'summary': {
                'total_images_tested': len(self.results['image_ids']),
                'mean_local_latency': statistics.mean(self.results['local_latencies']) 
                    if self.results['local_latencies'] else 0,
                'mean_cloud_latency': statistics.mean(self.results['cloud_latencies'])
                    if self.results['cloud_latencies'] else 0,
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved to: {output_file}")
        return report


async def run_comprehensive_benchmark(
    api_url: str,
    test_image: str = None,
    sample_size: int = 10
):
    """Run comprehensive benchmark suite"""
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║        ImageSearch Comprehensive Benchmark Suite             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    benchmark = ImageSearchBenchmark(api_url)
    
    # Use test image if provided, otherwise look for one
    if not test_image:
        test_image = "test_image.jpg"
        if not Path(test_image).exists():
            print(f"WARNING: Test image not found at {test_image}")
            print("Please provide --test-image path or place test_image.jpg in current directory")
            return
    
    # 1. Caption Latency Benchmark
    latency_stats = await benchmark.benchmark_caption_latency(test_image, num_runs=sample_size)
    
    # 2. Search Benchmark
    test_queries = [
        "a dog playing in the park",
        "sunset over mountains",
        "city skyline at night",
        "person using computer",
        "food on a table"
    ]
    search_stats = await benchmark.benchmark_search_latency(test_queries)
    
    # 3. Cost Estimation
    cost_scenarios = []
    for cloud_pct in [0.0, 0.1, 0.2, 0.3, 0.5, 1.0]:
        scenario = benchmark.estimate_cost(
            num_images=10000,
            cloud_percentage=cloud_pct,
            cost_per_1m_tokens=0.15  # GPT-4o-mini pricing
        )
        cost_scenarios.append(scenario)
    
    # 4. Generate visualizations
    if PLOTTING_AVAILABLE:
        print(f"\n{'='*60}")
        print("Generating Visualizations")
        print(f"{'='*60}")
        benchmark.plot_cost_quality_tradeoff(cost_scenarios)
    
    # 5. Generate report
    report = benchmark.generate_report()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                 Benchmark Complete!                          ║
╚══════════════════════════════════════════════════════════════╝

Summary:
  ✓ Caption latency tested: {sample_size} runs
  ✓ Search queries tested: {len(test_queries)} queries
  ✓ Cost scenarios analyzed: {len(cost_scenarios)} scenarios
  ✓ Report generated: benchmark_report.json
  
Key Findings:
  • Mean caption latency: {latency_stats['mean']:.2f}ms
  • P95 caption latency:  {latency_stats['p95']:.2f}ms
  • Mean search latency:  {search_stats['mean_latency']:.2f}ms
  • Cost at 20% cloud:    ${cost_scenarios[2]['cost_per_1k']:.4f} per 1K images

Next Steps:
  1. Review benchmark_report.json for detailed results
  2. Check generated plots (if matplotlib available)
  3. Adjust routing policy based on cost/latency tradeoffs
  4. Run with larger sample sizes for production estimates
    """)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark ImageSearch performance, quality, and costs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic benchmark with 10 samples
  python benchmark.py --test-image test.jpg
  
  # Extended benchmark with 100 samples
  python benchmark.py --test-image test.jpg --sample-size 100
  
  # Custom API endpoint
  python benchmark.py --api-url http://production:8000 --test-image test.jpg
        """
    )
    
    parser.add_argument(
        '--api-url',
        default='http://localhost:8000',
        help='API URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--test-image',
        help='Path to test image (default: test_image.jpg)'
    )
    parser.add_argument(
        '--sample-size',
        type=int,
        default=10,
        help='Number of samples for latency tests (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    print("Checking dependencies...")
    print(f"  Plotting (matplotlib/seaborn): {'✓' if PLOTTING_AVAILABLE else '✗ (optional)'}")
    print(f"  Analysis (pandas):             {'✓' if PANDAS_AVAILABLE else '✗ (optional)'}")
    print(f"  Quality metrics (NLTK):        {'✓' if NLTK_AVAILABLE else '✗ (optional)'}")
    print()
    
    asyncio.run(run_comprehensive_benchmark(
        api_url=args.api_url,
        test_image=args.test_image,
        sample_size=args.sample_size
    ))


if __name__ == "__main__":
    main()
