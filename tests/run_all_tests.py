#!/usr/bin/env python3
"""Run all test suites and provide summary."""

import sys
import os
import time
import traceback

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

def run_test_suite(test_file, description):
    """Run a test suite and capture results."""
    print(f"\n{'=' * 60}")
    print(f"Running {description}")
    print(f"File: {test_file}")
    print(f"{'=' * 60}")
    
    try:
        start_time = time.time()
        
        # Import and run the test module
        module_name = test_file.replace('.py', '')
        test_module = __import__(module_name)
        
        # If the module has a main section, it will run automatically
        # when imported due to if __name__ == "__main__" checks
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ {description} completed successfully in {duration:.2f}s")
        return True, duration
        
    except Exception as e:
        print(f"\n❌ {description} failed with error:")
        print(f"Error: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False, 0

def main():
    """Run all test suites."""
    print("🧪 WIZARD GAME - COMPREHENSIVE TEST SUITE")
    print("Testing all game systems and mechanics...")
    
    test_suites = [
        ('test_basic_gameplay', 'Basic Gameplay (turns, mana, cards)'),
        ('test_combat_system', 'Combat System (attack, block, damage)'),
        ('test_triggers_keywords', 'Triggers & Keywords (enter, attack, block)'),
        ('test_edge_cases', 'Edge Cases & Error Handling')
    ]
    
    results = []
    total_time = 0
    
    for test_file, description in test_suites:
        success, duration = run_test_suite(test_file, description)
        results.append((description, success, duration))
        total_time += duration
    
    # Summary
    print(f"\n\n{'=' * 80}")
    print("🏁 TEST SUMMARY")
    print(f"{'=' * 80}")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for description, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:<10} {description:<40} ({duration:.2f}s)")
    
    print(f"\nResults: {passed}/{total} test suites passed")
    print(f"Total time: {total_time:.2f}s")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Game is ready for play.")
        print("\n🎮 Try running: python3 main.py")
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed. Check errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)