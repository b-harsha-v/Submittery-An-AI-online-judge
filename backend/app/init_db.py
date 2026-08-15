import sys
import os
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models.user import User, UserRole
from .models.problem import Problem, TestCase, ProblemDifficulty
from .security import hash_password

def init_database():
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

def seed_data():
    db = SessionLocal()
    try:
        # Check if users already exist
        if db.query(User).first():
            print("Database already seeded. Skipping...")
            return

        print("Seeding users...")
        # Create Admin
        admin = User(
            email="admin@submittery.com",
            username="admin",
            hashed_password=hash_password("adminpass"),
            role=UserRole.ADMIN,
            avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=admin"
        )
        # Create Standard User
        user = User(
            email="user@submittery.com",
            username="coder123",
            hashed_password=hash_password("userpass"),
            role=UserRole.USER,
            avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=user"
        )
        db.add(admin)
        db.add(user)
        db.commit()

        print("Seeding problems...")
        
        # 1. Two Sum
        two_sum = Problem(
            title="Two Sum",
            slug="two-sum",
            description=r"""Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

### Input Format
- First line: Space-separated integers representing the array `nums`.
- Second line: A single integer representing `target`.

### Output Format
- Print the two indices (0-indexed) separated by a space (e.g. `0 1`). Order does not matter.

### Constraints
- $2 \le \text{nums.length} \le 10^4$
- $-10^9 \le \text{nums}[i] \le 10^9$
- $-10^9 \le \text{target} \le 10^9$
- Only one valid answer exists.
""",
            difficulty=ProblemDifficulty.EASY,
            time_limit=1.0,
            memory_limit=256,
            tags=["array", "hash-table"],
            starter_code={
                "python": """import sys

def solve():
    # Read inputs from standard input
    lines = sys.stdin.read().splitlines()
    if not lines or len(lines) < 2:
        return
        
    nums = list(map(int, lines[0].split()))
    target = int(lines[1])
    
    # Write your logic here
    # Example output: print("0 1")
    pass

if __name__ == '__main__':
    solve()
"""
            }
        )
        db.add(two_sum)
        db.flush() # Populate ID

        two_sum_cases = [
            TestCase(problem_id=two_sum.id, input="2 7 11 15\n9", expected_output="0 1", is_sample=True),
            TestCase(problem_id=two_sum.id, input="3 2 4\n6", expected_output="1 2", is_sample=True),
            TestCase(problem_id=two_sum.id, input="3 3\n6", expected_output="0 1", is_sample=False),
            TestCase(problem_id=two_sum.id, input="1 5 8 12 14\n20", expected_output="2 3", is_sample=False)
        ]
        db.bulk_save_objects(two_sum_cases)

        # 2. Reverse String
        reverse_string = Problem(
            title="Reverse String",
            slug="reverse-string",
            description=r"""Write a function that reverses a string. The input string is given as a single line.

### Input Format
- A single line containing a string.

### Output Format
- The reversed string.

### Constraints
- $1 \le \text{length} \le 10^5$
- The string consists of printable ASCII characters.
""",
            difficulty=ProblemDifficulty.EASY,
            time_limit=1.0,
            memory_limit=256,
            tags=["string", "two-pointers"],
            starter_code={
                "python": """import sys

def solve():
    # Read input from standard input
    input_str = sys.stdin.read().strip()
    if not input_str:
        return
        
    # Write your logic here
    pass

if __name__ == '__main__':
    solve()
"""
            }
        )
        db.add(reverse_string)
        db.flush()

        reverse_cases = [
            TestCase(problem_id=reverse_string.id, input="hello", expected_output="olleh", is_sample=True),
            TestCase(problem_id=reverse_string.id, input="Hannah", expected_output="hannaH", is_sample=True),
            TestCase(problem_id=reverse_string.id, input="a", expected_output="a", is_sample=False),
            TestCase(problem_id=reverse_string.id, input="Submittery v2", expected_output="2v yrettimbuS", is_sample=False)
        ]
        db.bulk_save_objects(reverse_cases)

        # 3. Binary Search
        binary_search = Problem(
            title="Binary Search",
            slug="binary-search",
            description=r"""Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, then return its index. Otherwise, return `-1`.

You must write an algorithm with $O(\log n)$ runtime complexity.

### Input Format
- First line: A single integer representing `target`.
- Second line: Space-separated sorted integers representing the array `nums`.

### Output Format
- A single integer representing the index of `target` or `-1`.

### Constraints
- $1 \le \text{nums.length} \le 10^4$
- $-10^4 < \text{nums}[i], \text{target} < 10^4$
- All the integers in `nums` are unique.
- `nums` is sorted in ascending order.
""",
            difficulty=ProblemDifficulty.EASY,
            time_limit=1.0,
            memory_limit=256,
            tags=["binary-search", "array"],
            starter_code={
                "python": """import sys

def solve():
    lines = sys.stdin.read().splitlines()
    if not lines or len(lines) < 2:
        return
        
    target = int(lines[0])
    nums = list(map(int, lines[1].split()))
    
    # Write your logic here
    pass

if __name__ == '__main__':
    solve()
"""
            }
        )
        db.add(binary_search)
        db.flush()

        binary_cases = [
            TestCase(problem_id=binary_search.id, input="9\n-1 0 3 5 9 12", expected_output="4", is_sample=True),
            TestCase(problem_id=binary_search.id, input="2\n-1 0 3 5 9 12", expected_output="-1", is_sample=True),
            TestCase(problem_id=binary_search.id, input="5\n5", expected_output="0", is_sample=False),
            TestCase(problem_id=binary_search.id, input="10\n1 2 3 4 5 6 7 8 9 11 12", expected_output="-1", is_sample=False)
        ]
        db.bulk_save_objects(binary_cases)

        # 4. Valid Parentheses
        valid_parentheses = Problem(
            title="Valid Parentheses",
            slug="valid-parentheses",
            description=r"""Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.

### Input Format
- A single line containing the string `s`.

### Output Format
- Print `true` if the brackets are valid, otherwise `false`.

### Constraints
- $1 \le \text{s.length} \le 10^4$
- `s` consists of parentheses characters only.
""",
            difficulty=ProblemDifficulty.EASY,
            time_limit=1.0,
            memory_limit=256,
            tags=["string", "stack"],
            starter_code={
                "python": """import sys

def solve():
    s = sys.stdin.read().strip()
    if not s:
        print("true")
        return
        
    # Write your logic here
    # Example: print("true" or "false")
    pass

if __name__ == '__main__':
    solve()
"""
            }
        )
        db.add(valid_parentheses)
        db.flush()

        parentheses_cases = [
            TestCase(problem_id=valid_parentheses.id, input="()", expected_output="true", is_sample=True),
            TestCase(problem_id=valid_parentheses.id, input="()[]{}", expected_output="true", is_sample=True),
            TestCase(problem_id=valid_parentheses.id, input="(]", expected_output="false", is_sample=True),
            TestCase(problem_id=valid_parentheses.id, input="([)]", expected_output="false", is_sample=False),
            TestCase(problem_id=valid_parentheses.id, input="{[]}", expected_output="true", is_sample=False)
        ]
        db.bulk_save_objects(parentheses_cases)

        # 5. Fibonacci Number
        fibonacci = Problem(
            title="Fibonacci Number",
            slug="fibonacci-number",
            description=r"""The Fibonacci numbers, commonly denoted $F(n)$ form a sequence, called the Fibonacci sequence, such that each number is the sum of the two preceding ones, starting from 0 and 1. That is:
- $F(0) = 0, F(1) = 1$
- $F(n) = F(n - 1) + F(n - 2)$, for $n > 1$.

Given $n$, calculate $F(n)$.

### Input Format
- A single line containing an integer $n$.

### Output Format
- A single integer representing $F(n)$.

### Constraints
- $0 \le n \le 30$
""",
            difficulty=ProblemDifficulty.EASY,
            time_limit=1.0,
            memory_limit=256,
            tags=["math", "dynamic-programming"],
            starter_code={
                "python": """import sys

def solve():
    line = sys.stdin.read().strip()
    if not line:
        return
    n = int(line)
    
    # Write your logic here
    pass

if __name__ == '__main__':
    solve()
"""
            }
        )
        db.add(fibonacci)
        db.flush()

        fib_cases = [
            TestCase(problem_id=fibonacci.id, input="2", expected_output="1", is_sample=True),
            TestCase(problem_id=fibonacci.id, input="3", expected_output="2", is_sample=True),
            TestCase(problem_id=fibonacci.id, input="4", expected_output="3", is_sample=True),
            TestCase(problem_id=fibonacci.id, input="0", expected_output="0", is_sample=False),
            TestCase(problem_id=fibonacci.id, input="30", expected_output="832040", is_sample=False)
        ]
        db.bulk_save_objects(fib_cases)

        # 6. Contains Duplicate (Arrays & Hashing)
        contains_duplicate = Problem(
            title="Contains Duplicate",
            slug="contains-duplicate",
            description=r"""Given an integer array `nums`, return `true` if any value appears at least twice in the array, and return `false` if every element is distinct.

### Input Format
- A single line containing space-separated integers representing the array `nums`.

### Output Format
- `true` or `false`.

### Constraints
- $1 \le \text{nums.length} \le 10^5$
- $-10^9 \le \text{nums}[i] \le 10^9$
""",
            difficulty=ProblemDifficulty.EASY,
            time_limit=1.0,
            memory_limit=256,
            tags=["array", "hash-table"],
            starter_code={
                "python": """import sys

def solve():
    # Read inputs from standard input
    input_str = sys.stdin.read().strip()
    if not input_str:
        return
        
    nums = list(map(int, input_str.split()))
    
    # Write your logic here
    pass

if __name__ == '__main__':
    solve()
"""
            }
        )
        db.add(contains_duplicate)
        db.flush()

        dup_cases = [
            TestCase(problem_id=contains_duplicate.id, input="1 2 3 1", expected_output="true", is_sample=True),
            TestCase(problem_id=contains_duplicate.id, input="1 2 3 4", expected_output="false", is_sample=True),
            TestCase(problem_id=contains_duplicate.id, input="1 1 1 3 3 4 3 2 4 2", expected_output="true", is_sample=False),
            TestCase(problem_id=contains_duplicate.id, input="10", expected_output="false", is_sample=False)
        ]
        db.bulk_save_objects(dup_cases)

        # 7. Container With Most Water (Two Pointers)
        most_water = Problem(
            title="Container With Most Water",
            slug="container-with-most-water",
            description=r"""You are given an integer array `height` of length `n`. There are `n` vertical lines drawn such that the two endpoints of the $i^{\text{th}}$ line are $(i, 0)$ and $(i, \text{height}[i])$.

Find two lines that together with the x-axis form a container, such that the container contains the most water.

Return the maximum amount of water a container can store.

### Input Format
- A single line of space-separated integers representing the `height` array.

### Output Format
- A single integer representing the maximum water.

### Constraints
- $2 \le n \le 10^5$
- $0 \le \text{height}[i] \le 10^4$
""",
            difficulty=ProblemDifficulty.MEDIUM,
            time_limit=1.0,
            memory_limit=256,
            tags=["two-pointers", "array"],
            starter_code={
                "python": """import sys

def solve():
    # Read inputs from standard input
    input_str = sys.stdin.read().strip()
    if not input_str:
        return
        
    height = list(map(int, input_str.split()))
    
    # Write your logic here
    pass

if __name__ == '__main__':
    solve()
"""
            }
        )
        db.add(most_water)
        db.flush()

        water_cases = [
            TestCase(problem_id=most_water.id, input="1 8 6 2 5 4 8 3 7", expected_output="49", is_sample=True),
            TestCase(problem_id=most_water.id, input="1 1", expected_output="1", is_sample=True),
            TestCase(problem_id=most_water.id, input="4 3 2 1 4", expected_output="16", is_sample=False),
            TestCase(problem_id=most_water.id, input="1 2 1", expected_output="2", is_sample=False)
        ]
        db.bulk_save_objects(water_cases)

        db.commit()
        print("Database successfully seeded with starter problems!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == '__main__':
    init_database()
    seed_data()
