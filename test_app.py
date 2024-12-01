import unittest
import time
from app import fetch_all_star_data, quadrants, fetch_star_data

class TestFetchAllStarData(unittest.TestCase):
    
    def test_speedup(self):
        # Measure time for sequential execution
        start_time = time.time()
        sequential_results = fetch_all_star_data(quadrants, num_processes=1)
        sequential_time = time.time() - start_time
        
        # Measure time for parallel execution with 2 processes
        start_time = time.time()
        parallel_results_2 = fetch_all_star_data(quadrants, num_processes=2)
        parallel_time_2 = time.time() - start_time
        
        # Measure time for parallel execution with 3 processes
        start_time = time.time()
        parallel_results_3 = fetch_all_star_data(quadrants, num_processes=3)
        parallel_time_3 = time.time() - start_time
        
        # Measure time for parallel execution with 4 processes
        start_time = time.time()
        parallel_results_4 = fetch_all_star_data(quadrants, num_processes=4)
        parallel_time_4 = time.time() - start_time
        
        # Check if parallel execution is faster
        self.assertTrue(parallel_time_4 < sequential_time, "Parallel execution with 4 processes should be faster than sequential execution")
        print(f"Sequential Time: {sequential_time}")
        print(f"Parallel Time with 2 processes: {parallel_time_2}")
        print(f"Parallel Time with 3 processes: {parallel_time_3}")
        print(f"Parallel Time with 4 processes: {parallel_time_4}")

if __name__ == '__main__':
    unittest.main()