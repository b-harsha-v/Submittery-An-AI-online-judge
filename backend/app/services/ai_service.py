import os
import numpy as np
from sqlalchemy.orm import Session
from ..config import settings
from ..models.problem import Problem
from ..models.submission import Submission

# Try importing the new Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    client_available = True
except ImportError:
    client_available = False

class AIService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        
        if client_available and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                print("[*] Gemini Client initialized successfully with API key.")
            except Exception as e:
                print(f"[!] Error initializing Gemini Client: {e}")

    def is_active(self) -> bool:
        return self.client is not None

    def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generates content from Gemini or falls back to mock responses.
        """
        if self.is_active():
            try:
                config = {}
                if system_instruction:
                    config["system_instruction"] = system_instruction
                
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=config
                )
                return response.text
            except Exception as e:
                print(f"[!] Gemini generation error: {e}")
                return f"[Gemini Error: {str(e)}]. Switched to Mock Mode."
        
        # Fallback to Mock Response Generator
        return self._generate_mock_response(prompt, system_instruction)

    def get_embedding(self, text: str) -> list:
        """
        Gets embedding vector for text using Gemini.
        Returns list of floats or mock vector of length 768.
        """
        if self.is_active():
            try:
                response = self.client.models.embed_content(
                    model='text-embedding-004',
                    contents=text
                )
                # response.embeddings contains embedding objects
                if response.embeddings:
                    return response.embeddings[0].values
            except Exception as e:
                print(f"[!] Embedding error: {e}")
        
        # Mock embedding: deterministic vector based on text length and character sums
        np.random.seed(abs(hash(text)) % (2**32))
        return np.random.rand(768).tolist()

    # --- MAIN AI FEATURES ---

    def analyze_complexity(self, code: str, problem_title: str) -> str:
        system = "You are an expert algorithm educator. Analyze the time and space complexity of the provided user code."
        prompt = f"""Problem: {problem_title}
User Code:
```python
{code}
```

Identify the Big-O Time Complexity and Space Complexity. Suggest any optimizations if possible. Keep it educational and concise.
"""
        return self.generate_response(prompt, system)

    def provide_code_review(self, code: str, problem_title: str, submission_status: str) -> str:
        system = "You are a senior software engineer conducting a peer code review. Focus on best practices, readability, naming conventions, and cleanliness."
        prompt = f"""Problem: {problem_title}
Submission Verdict: {submission_status}
User Code:
```python
{code}
```

Provide a constructive code review. Detail:
1. What went well (naming, logic).
2. Readability improvements.
3. Best practices (e.g. edge cases, pythonic structures).
"""
        return self.generate_response(prompt, system)

    def generate_debug_hints(self, code: str, problem_title: str, error_message: str) -> str:
        system = "You are a coding debugging mentor. Do NOT provide the complete corrected solution code. Instead, explain the error conceptually and give progressive, guiding hints to help the student solve it."
        prompt = f"""Problem: {problem_title}
Error Message / Failure: {error_message}
User Code:
```python
{code}
```

Explain what is causing this issue and provide 2-3 progressive hints. Again, do NOT write the corrected code.
"""
        return self.generate_response(prompt, system)

    def answer_question(self, query: str, problem: Problem, history: list = None) -> str:
        """
        RAG-grounded QA. Injects problem description, constraints, and editorials.
        """
        system = "You are a computer science teaching assistant. Answer the student's question, grounding your response strictly in the provided Problem Context. Do not hallucinate algorithms."
        
        context = f"""PROBLEM CONTEXT:
Title: {problem.title}
Difficulty: {problem.difficulty.value if hasattr(problem.difficulty, 'value') else problem.difficulty}
Description:
{problem.description}
Tags: {problem.tags}
"""
        prompt = f"""{context}

Student Question: {query}
"""
        return self.generate_response(prompt, system)

    def recommend_problems(self, current_problem: Problem, all_problems: list) -> list:
        """
        Uses RAG / semantic similarity.
        Compares embedding of current problem's description/tags with other problems.
        Returns top-2 recommended problems.
        """
        if len(all_problems) <= 1:
            return []
            
        current_vector = self.get_embedding(f"{current_problem.title} {' '.join(current_problem.tags or [])}")
        current_np = np.array(current_vector)
        
        scored_problems = []
        for p in all_problems:
            if p.id == current_problem.id:
                continue
            
            p_vector = self.get_embedding(f"{p.title} {' '.join(p.tags or [])}")
            p_np = np.array(p_vector)
            
            # Cosine similarity
            dot_product = np.dot(current_np, p_np)
            norm_a = np.linalg.norm(current_np)
            norm_b = np.linalg.norm(p_np)
            similarity = dot_product / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
            
            scored_problems.append((similarity, p))
            
        # Sort by similarity descending
        scored_problems.sort(key=lambda x: x[0], reverse=True)
        # Return top 2 problems
        return [p for score, p in scored_problems[:2]]

    # --- MOCK RESPONSE ENGINE ---

    def _generate_mock_response(self, prompt: str, system: str) -> str:
        prompt_lower = prompt.lower()
        
        # Check if Two Sum
        is_two_sum = "two sum" in prompt_lower
        is_reverse_string = "reverse string" in prompt_lower or "reverse-string" in prompt_lower
        is_binary_search = "binary search" in prompt_lower or "binary-search" in prompt_lower
        is_valid_parentheses = "valid parentheses" in prompt_lower or "valid-parentheses" in prompt_lower
        is_fibonacci = "fibonacci" in prompt_lower
        
        # Review Mode
        if "code review" in prompt_lower or "review" in system.lower():
            if is_two_sum:
                return """### 🤖 AI Code Review (Mock Mode)

**Overview**: Your solution for **Two Sum** looks solid. Let's analyze its readability and pythonic conventions.

**1. Strengths**:
- Logic for index tracking is present.
- Good variable naming (e.g. using `nums` and `target` matching the problem description).

**2. Readability Improvements**:
- If you used a nested loop ($O(N^2)$), consider extracting it into a single-pass hash map to improve performance.
- Use Python's `enumerate()` for cleaner index handling rather than a manual counter:
  ```python
  for index, value in enumerate(nums):
      # code...
  ```

**3. Best Practices**:
- Consider adding type hinting: `def two_sum(nums: list[int], target: int) -> list[int]`.
- Always check if inputs can be empty or have fewer than two elements as defensive validation.
"""
            elif is_reverse_string:
                return """### 🤖 AI Code Review (Mock Mode)

**Overview**: Nice job on reversing the string.
- If you used `s[::-1]`, that is the most efficient and pythonic way in CPython.
- If you used a two-pointer approach, it displays strong algorithmic fundamentals!
"""
            else:
                return "### 🤖 AI Code Review (Mock Mode)\nYour solution looks clean and correct. Pay attention to edge cases like empty inputs, single element arrays, and integer overflow constraints."

        # Complexity Mode
        elif "complexity" in prompt_lower or "complexity" in system.lower():
            if "for " in prompt and "for " in prompt.split("for ", 1)[1]: # nested loop heuristic
                return """### 📊 Complexity Analysis (Mock Mode)

- **Time Complexity**: $\mathcal{O}(N^2)$ where $N$ is the length of the input. This is due to the nested loop scanning all pairs.
- **Space Complexity**: $\mathcal{O}(1)$ since you are using only a constant amount of extra memory space.
- **Optimization**: You can reduce the time complexity to $\mathcal{O}(N)$ using a Hash Map to store numbers and their indices!
"""
            else:
                return """### 📊 Complexity Analysis (Mock Mode)

- **Time Complexity**: $\mathcal{O}(N)$ where $N$ is the number of elements. We traverse the input array exactly once.
- **Space Complexity**: $\mathcal{O}(N)$ in the worst case to store the visited items in our Hash Map.
"""

        # Debug Mode
        elif "debug" in prompt_lower or "debug" in system.lower():
            return """### 🔧 Debugger Assistant (Mock Mode)

It looks like your code encountered a failure or didn't produce the expected output.
- **Hint 1**: Trace the execution for the smallest input (e.g., list of size 2, or an empty string).
- **Hint 2**: Check if you are double-using the same element. Remember, you cannot use the same index twice.
- **Hint 3**: Print out the state of variables right before the return statement to verify if they match expectations.
"""

        # General Question Answering
        else:
            return """### 💡 AI Mentor Response (Mock Mode)

I am here to help you study coding algorithms!
- To optimize your code, try to use a Hash Map to trade space for time (reducing $\mathcal{O}(N^2)$ to $\mathcal{O}(N)$).
- Make sure to handle potential boundary conditions (like target values that are negative, or elements not found).
- Let me know if you would like a code review, complexity analysis, or debugging hints for your submission!
"""

ai_service = AIService()
