# Project Requirements Specifications — Submittery v3

This document outlines the functional and non-functional requirements of the **Submittery** platform. It acts as a reference specification for the development team and execution workers.

---

## 1. Project Goal
Submittery is an AI-powered Online Code Judge and low-latency Real-time Collaborative Pair Programming platform. It enables users to browse algorithmic coding problems, code solutions in Monaco Editor, execute code safely inside isolated sandboxes, and pair program with peers using synchronized editor sessions.

---

## 2. Functional Requirements

### A. Authentication & User Profile Management
- **User Authentication**: Secure signup and login flow using JWT (JSON Web Tokens). Support mock Google OAuth authentication.
- **Role-Based Access Control**:
  - **Standard User**: Can browse problems, solve them, view their own runs, and participate in collaborative rooms.
  - **Admin**: Can additionally access the Admin Workspace Console and seed/create new coding problems.
- **Account Settings**: Users must be able to change their username, email address, password, and customize their robot avatar seed (Dicebear API) with a real-time visual preview.

### B. Problems Catalog (Dashboard)
- **Problem Retrieval**: Table listing all seeded problems with difficulty levels (Easy, Medium, Hard), tags, and dynamic order index numbering.
- **Topic-wise Filters (NeetCode 150)**: Topic dropdown to filter catalog items dynamically by category (e.g. Arrays & Hashing, Two Pointers, Stack, Binary Search, 1-D DP).
- **Difficulty & Search Filters**: Real-time filtering chips by difficulty levels and a search bar for problem names.
- **Dynamic Stats Board**: Computes solved counts and difficulty ratios (solved vs. total) dynamically based on user's accepted submission history.

### C. Drag-Resizable Workspace Layout
- **Three-Pane Splitting**:
  - **Left details panel**: Tabs for Markdown problem description, Submissions log, and AI explain page.
  - **Top-right editor pane**: Monaco Editor workspace.
  - **Bottom-right console pane**: Submissions logs, AI output, and discussions.
- **Responsive Splitters**: Draggable vertical divider handle separating left/right splits and horizontal handle separating editor/console drawer splits. Re-trigger Monaco layout sizing adjustments during drags.

### D. Safe Code Sandboxing & Execution (Compiler Service)
- **Isolated Containers**: Spawns ephemeral Docker sandbox containers (e.g., `submittery_sandbox`) for each solution evaluation to prevent Remote Code Execution (RCE) on host filesystems.
- **Limit Enforcement**: Restrict process boundaries by applying CPU execution time limits (e.g. 1.0s) and RSS memory usage limits (e.g. 256MB).
- **Asynchronous Task Queue**: Uses a Redis messaging queue (`submissions_queue`) to dispatch code evaluation requests. A background queue worker executes jobs sequentially and publishes verdict changes back via Redis Pub/Sub channels.

### E. Detailed Test Case Verdicts
- **Dynamic Case-by-Case Visualizer**: Compiles and displays outputs for each test case individually under "Verdict Output" tabs.
- **Verdict Categorization**: Classifies evaluations into:
  - `ACCEPTED (AC)`: Code executes correctly and matches output.
  - `WRONG ANSWER (WA)`: Output mismatch.
  - `TIME LIMIT EXCEEDED (TLE)`: Process exceeds time boundary.
  - `MEMORY LIMIT EXCEEDED (MLE)`: Process memory usage exceeds boundary.
  - `RUNTIME ERROR (RE)`: Code execution fails with stack trace/errors.
  - `COMPILATION ERROR (CE)`: Failures during compilation/syntax check.
- **Execution Counters**: Appends the count of passed test cases over the total number of test cases (e.g. `ACCEPTED (4/4 Cases Passed)` or `WRONG ANSWER (2/4 Cases Passed)`) next to the verdict status badge.

### F. Real-Time Pair Programming Lobby (WebSockets)
- **Lobby Sessions**: Generate unique room codes to allow multiple developers to join a workspace.
- **Synchronization**: Use WebSocket connections to synchronize editor code modifications and handle cursor telemetry tracks across concurrent peers.

### G. AI Coder Mentor Integration (Gemini API)
- **Explain Module**: Summarize problem constraints, input/output styles, and general algorithmic approach directions.
- **Code Review**: Analyze submitted solutions and suggest time/space complexity optimizations.
- **Debugging Hints**: Stream debug hints to users when their code hits failing verdicts (WA, TLE, MLE, RE).

### H. Multi-Theme Options
- **Light/Dark Mode Toggles**: sun/moon switcher to flip layout colors.
- **Theme Color Bindings**: Black/White card themes, light purple headers, and Monaco Editor theme switching (`vs` for light, `vs-dark` for dark).

---

## 3. Non-Functional Requirements

### A. Security
- Complete container isolation for code execution. Under no circumstances should untrusted user code have access to the host's files, environment variables, or private networks.
- Secure password hashing using `bcrypt` and tokenized request headers.

### B. Scalability & Latency
- Asynchronous task processing via Redis to keep the web server responsive under heavy submission volume.
- Low-latency WebSocket connections for real-time pair programming updates (messages dispatched under 50ms).

### C. Performance & Reliability
- Automatic database transaction rollback (`db.rollback()`) on worker execution failures to prevent corrupted state.
- Graceful reconnection attempts if Redis or database connections go offline.
