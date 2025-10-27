# ImageSearch Benchmarks

This directory contains benchmarking tools for evaluating the ImageSearch system's performance, quality, and cost characteristics.

## Files

### benchmark.py
Comprehensive benchmark script for testing:
- **Caption latency** (local vs cloud)
- **Search performance** (latency and recall)
- **Cost estimation** (various cloud usage scenarios)
- **Quality metrics** (BLEU, METEOR scores)

### benchmark.ipynb
Jupyter notebook placeholder (can be created from benchmark.py)

## Usage

### Prerequisites

Install dependencies:
```bash
pip install -r ../apps/api/requirements.txt
```

### Running Benchmarks

**Basic benchmark** (10 samples):
```bash
python benchmark.py --test-image ../test_image.jpg
```

**Extended benchmark** (100 samples):
```bash
python benchmark.py --test-image ../test_image.jpg --sample-size 100
```

**Custom API endpoint**:
```bash
python benchmark.py --api-url http://production:8000 --test-image test.jpg
```

### Output

The benchmark generates:
- **benchmark_report.json** - Detailed JSON report with all metrics
- **latency_distribution.png** - Histogram of caption latencies
- **cost_quality_tradeoff.png** - Cost vs quality analysis plots

## Metrics

### Latency Metrics
- Mean, median, P95, P99 latencies
- Standard deviation
- Min/max values

### Cost Estimation
- Cost per 1K images
- Total cost projections
- Cloud vs local usage ratios

### Quality Metrics (requires NLTK)
- **BLEU score** - Similarity to reference captions
- **METEOR score** - Semantic similarity metric

## Example Output

```
╔══════════════════════════════════════════════════════════════╗
║        ImageSearch Comprehensive Benchmark Suite             ║
╚══════════════════════════════════════════════════════════════╝

============================================================
Benchmarking Caption Latency (10 runs)
============================================================
Run 1/10: 234.56ms - local - A dog sitting on grass in a park...
Run 2/10: 198.32ms - local - A dog sitting on grass in a park...
...

Latency Statistics:
  Mean:   215.43ms
  Median: 210.12ms
  P95:    245.67ms
  P99:    256.89ms
  StdDev: 18.34ms

============================================================
Cost Estimation
============================================================
Scenario: 10,000 images, 20% cloud
  Local images:  8,000 (free)
  Cloud images:  2,000
  Total tokens:  1,000,000
  Total cost:    $0.1500
  Cost per 1K:   $0.0150
```

## Converting to Jupyter Notebook

To convert the Python script to a Jupyter notebook:

```bash
# Install jupytext
pip install jupytext

# Convert
jupytext --to notebook benchmark.py
```

## Advanced Usage

### Custom Quality Evaluation

Edit `benchmark.py` to add custom quality metrics:

```python
def calculate_custom_metric(generated: str, reference: str) -> float:
    # Your custom metric
    return score

benchmark.calculate_custom_metric = calculate_custom_metric
```

### Batch Processing

For testing many images:

```python
import asyncio
from benchmark import ImageSearchBenchmark

async def batch_test():
    benchmark = ImageSearchBenchmark()
    for img_path in image_paths:
        await benchmark.benchmark_caption_latency(img_path, num_runs=5)

asyncio.run(batch_test())
```

## Troubleshooting

**Issue**: Plots not generating
- **Solution**: Install matplotlib and seaborn: `pip install matplotlib seaborn`

**Issue**: Quality metrics not working
- **Solution**: Install NLTK and download data:
  ```bash
  pip install nltk
  python -c "import nltk; nltk.download('wordnet'); nltk.download('punkt')"
  ```

**Issue**: Connection refused
- **Solution**: Ensure API is running: `uvicorn apps.api.main:app --port 8000`

## See Also

- [Main README](../README.md) - Project overview
- [SESSION-IMAGE-STORAGE-PLAN.md](../planing/SESSION-IMAGE-STORAGE-PLAN.md) - Implementation plan
- [test_image_storage.py](../tests/test_image_storage.py) - Integration tests
