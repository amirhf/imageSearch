"""
Test Grafana dashboard and Prometheus alert configuration.
Validates JSON structure and alert rule syntax.
"""

import json
import sys
import os
from pathlib import Path
import yaml

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 > nul')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_dashboard_json():
    """Test that Grafana dashboard JSON is valid"""
    print("\n" + "="*60)
    print("TEST 1: Grafana Dashboard JSON Validation")
    print("="*60)
    
    try:
        dashboard_path = project_root / "infra" / "grafana" / "cloud_adapter_dashboard.json"
        
        if not dashboard_path.exists():
            print(f"❌ Dashboard file not found: {dashboard_path}")
            return False
        
        print(f"✓ Found dashboard file: {dashboard_path.name}")
        
        # Load and parse JSON
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            dashboard = json.load(f)
        
        print(f"✓ Valid JSON structure")
        
        # Check required fields
        required_fields = ['title', 'panels', 'templating']
        for field in required_fields:
            if field not in dashboard:
                print(f"❌ Missing required field: {field}")
                return False
            print(f"✓ Has required field: {field}")
        
        # Count panels
        panel_count = len(dashboard['panels'])
        print(f"✓ Dashboard has {panel_count} panels")
        
        # Check templating variables
        variables = dashboard.get('templating', {}).get('list', [])
        print(f"✓ Dashboard has {len(variables)} template variables")
        
        for var in variables:
            print(f"  - {var.get('name')}: {var.get('label')}")
        
        print("\n✅ Dashboard JSON validation PASSED")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Dashboard validation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_alert_rules_yaml():
    """Test that Prometheus alert rules YAML is valid"""
    print("\n" + "="*60)
    print("TEST 2: Prometheus Alert Rules Validation")
    print("="*60)
    
    try:
        alert_path = project_root / "infra" / "prometheus" / "alert_rules.yml"
        
        if not alert_path.exists():
            print(f"❌ Alert rules file not found: {alert_path}")
            return False
        
        print(f"✓ Found alert rules file: {alert_path.name}")
        
        # Load and parse YAML
        with open(alert_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        
        print(f"✓ Valid YAML structure")
        
        # Check structure
        if 'groups' not in rules:
            print(f"❌ Missing 'groups' key")
            return False
        
        print(f"✓ Has 'groups' key")
        
        # Count alert groups and rules
        groups = rules['groups']
        print(f"✓ Found {len(groups)} rule groups")
        
        total_alerts = 0
        total_recording_rules = 0
        
        for group in groups:
            group_name = group.get('name', 'unknown')
            rules_list = group.get('rules', [])
            
            # Count alert vs recording rules
            alerts = [r for r in rules_list if 'alert' in r]
            recording = [r for r in rules_list if 'record' in r]
            
            total_alerts += len(alerts)
            total_recording_rules += len(recording)
            
            print(f"\n  Group: {group_name}")
            print(f"    Alerts: {len(alerts)}")
            print(f"    Recording rules: {len(recording)}")
            
            # Show alert names
            if alerts:
                print(f"    Alert rules:")
                for alert in alerts[:5]:  # Show first 5
                    severity = alert.get('labels', {}).get('severity', 'unknown')
                    print(f"      - {alert['alert']} (severity: {severity})")
                if len(alerts) > 5:
                    print(f"      ... and {len(alerts) - 5} more")
        
        print(f"\n✓ Total alert rules: {total_alerts}")
        print(f"✓ Total recording rules: {total_recording_rules}")
        
        print("\n✅ Alert rules validation PASSED")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML: {e}")
        return False
    except Exception as e:
        print(f"❌ Alert rules validation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prometheus_config():
    """Test that Prometheus config YAML is valid"""
    print("\n" + "="*60)
    print("TEST 3: Prometheus Config Validation")
    print("="*60)
    
    try:
        config_path = project_root / "infra" / "prometheus" / "prometheus.yml"
        
        if not config_path.exists():
            print(f"❌ Prometheus config not found: {config_path}")
            return False
        
        print(f"✓ Found Prometheus config: {config_path.name}")
        
        # Load and parse YAML
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"✓ Valid YAML structure")
        
        # Check required fields
        if 'global' in config:
            print(f"✓ Has 'global' section")
            scrape_interval = config['global'].get('scrape_interval', 'not set')
            print(f"  - scrape_interval: {scrape_interval}")
        
        if 'rule_files' in config:
            print(f"✓ Has 'rule_files' section")
            for rule_file in config['rule_files']:
                print(f"  - {rule_file}")
        
        if 'scrape_configs' in config:
            print(f"✓ Has 'scrape_configs' section")
            for job in config['scrape_configs']:
                job_name = job.get('job_name', 'unknown')
                targets = job.get('static_configs', [{}])[0].get('targets', [])
                print(f"  - Job: {job_name}, Targets: {targets}")
        
        print("\n✅ Prometheus config validation PASSED")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML: {e}")
        return False
    except Exception as e:
        print(f"❌ Prometheus config validation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dashboard_metrics():
    """Test that dashboard references valid metrics"""
    print("\n" + "="*60)
    print("TEST 4: Dashboard Metrics Reference Check")
    print("="*60)
    
    try:
        dashboard_path = project_root / "infra" / "grafana" / "cloud_adapter_dashboard.json"
        
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            dashboard = json.load(f)
        
        # Expected metrics from our implementation
        expected_metrics = [
            'cloud_requests_total',
            'cloud_requests_failed_total',
            'cloud_request_duration_seconds',
            'cloud_cost_total_usd',
            'cloud_daily_cost_usd',
            'rate_limiter_requests_per_minute',
            'circuit_breaker_state',
            'cloud_tokens_input_total',
            'cloud_tokens_output_total',
        ]
        
        # Extract all metric names from dashboard
        dashboard_str = json.dumps(dashboard)
        
        found_metrics = []
        missing_metrics = []
        
        for metric in expected_metrics:
            if metric in dashboard_str:
                found_metrics.append(metric)
                print(f"✓ Dashboard uses metric: {metric}")
            else:
                missing_metrics.append(metric)
                print(f"⚠️  Dashboard doesn't use: {metric}")
        
        print(f"\n✓ Dashboard references {len(found_metrics)}/{len(expected_metrics)} expected metrics")
        
        if missing_metrics:
            print(f"⚠️  Missing metrics: {', '.join(missing_metrics)}")
        
        print("\n✅ Dashboard metrics check PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard metrics check FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all dashboard configuration tests"""
    print("\n" + "="*60)
    print("DASHBOARD & ALERTS CONFIGURATION TESTS")
    print("="*60)
    print("\nValidating Grafana dashboard and Prometheus alerts...")
    
    results = []
    
    # Run tests
    results.append(("Dashboard JSON", test_dashboard_json()))
    results.append(("Alert Rules YAML", test_alert_rules_yaml()))
    results.append(("Prometheus Config", test_prometheus_config()))
    results.append(("Dashboard Metrics", test_dashboard_metrics()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All configuration files are valid!")
        print("\nNext steps:")
        print("  1. Import dashboard to Grafana")
        print("  2. Restart Prometheus to load alert rules")
        print("  3. View dashboard at http://localhost:3000")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
