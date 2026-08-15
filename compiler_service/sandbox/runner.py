import os
import sys
import json
import time
import subprocess
import resource

def run_test_case(code_path: str, input_data: str, expected_output: str, time_limit: float, memory_limit_mb: int):
    # Enforce memory limits if possible at the process level (RLIMIT_AS)
    # Memory limit in bytes
    mem_limit_bytes = memory_limit_mb * 1024 * 1024
    
    def set_limits():
        # Prevent fork bombs: limit max processes to e.g. 20
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (20, 20))
        except Exception:
            pass
        # Limit address space (memory limit)
        try:
            # We set virtual memory limit to 1.5x of memory limit to allow python VM startup overhead
            resource.setrlimit(resource.RLIMIT_AS, (int(mem_limit_bytes * 1.5), int(mem_limit_bytes * 1.5)))
        except Exception:
            pass

    start_time = time.perf_counter()
    
    # Run user script as a subprocess
    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, code_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=set_limits # Enforce limits right before child executes (Linux only)
        )
        
        # Pass input and wait for result with timeout
        stdout, stderr = process.communicate(input=input_data, timeout=time_limit)
        exit_code = process.returncode
        
    except subprocess.TimeoutExpired:
        if process:
            process.kill()
            stdout, stderr = process.communicate()
        return {
            "status": "time_limit_exceeded",
            "runtime": time_limit,
            "memory": 0,
            "error": "Time Limit Exceeded"
        }
    except Exception as e:
        if process:
            process.kill()
        return {
            "status": "runtime_error",
            "runtime": 0.0,
            "memory": 0,
            "error": f"Failed to execute process: {str(e)}"
        }

    end_time = time.perf_counter()
    duration = end_time - start_time
    
    # Measure memory usage using getrusage for child processes
    # On Linux, ru_maxrss is in Kilobytes
    rusage = resource.getrusage(resource.RUSAGE_CHILDREN)
    memory_used_kb = rusage.ru_maxrss
    
    # If the process crashed due to memory limit (or exit code was negative/terminated by signal)
    # On Unix, signals like SIGSEGV (11) or SIGKILL (9) indicate out of memory or segfault
    if exit_code != 0:
        status = "runtime_error"
        error_msg = stderr.strip() if stderr else f"Process exited with code {exit_code}"
        # Check if exited due to memory limit
        if memory_used_kb > memory_limit_mb * 1024 or "MemoryError" in error_msg:
            status = "memory_limit_exceeded"
            error_msg = "Memory Limit Exceeded"
        return {
            "status": status,
            "runtime": duration,
            "memory": memory_used_kb,
            "error": error_msg
        }

    # Compare output
    # Strip trailing whitespace and newlines for a lenient comparison
    cleaned_stdout = "\n".join([line.rstrip() for line in stdout.strip().splitlines()])
    cleaned_expected = "\n".join([line.rstrip() for line in expected_output.strip().splitlines()])
    
    if cleaned_stdout == cleaned_expected:
        return {
            "status": "accepted",
            "runtime": duration,
            "memory": memory_used_kb,
            "error": None
        }
    else:
        # Wrong answer
        # Return a snippet of output and expected output for debugging
        return {
            "status": "wrong_answer",
            "runtime": duration,
            "memory": memory_used_kb,
            "error": f"Expected: '{expected_output.strip()[:100]}', Got: '{stdout.strip()[:100]}'"
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python runner.py <config_json_path>")
        sys.exit(1)
        
    config_path = sys.argv[1]
    with open(config_path, "r") as f:
        config = json.load(f)
        
    code_path = config["code_path"]
    test_cases = config["test_cases"]
    time_limit = config["time_limit"]
    memory_limit = config["memory_limit"] # in MB
    
    results = []
    
    for tc in test_cases:
        res = run_test_case(
            code_path=code_path,
            input_data=tc["input"],
            expected_output=tc["expected_output"],
            time_limit=time_limit,
            memory_limit_mb=memory_limit
        )
        res["id"] = tc.get("id")
        results.append(res)
        
        # If any test case fails, we can stop early (standard online judge behavior)
        # to save execution resources and time.
        if res["status"] != "accepted":
            break
            
    # Print the final report as JSON to stdout
    print("---RESULT_START---")
    print(json.dumps(results))
    print("---RESULT_END---")

if __name__ == '__main__':
    main()
