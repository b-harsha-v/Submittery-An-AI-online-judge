# Submittery 🚀

An AI-powered, full-stack online judge for practicing competitive programming problems, built from the ground up.

## ✨ Key Features

### For Users
* **Problem Solving:** View a list of problems, solve them in a feature-rich Monaco editor (the same one that powers VS Code).
* **Multi-Language Support:** Submit solutions in C++, Python, and Java.
* **Custom Testcases:** A "Run" button to test code against custom inputs before final submission.
* **Instant Verdicts:** Get immediate feedback on submissions (`Accepted`, `Wrong Answer`, `Time Limit Exceeded`, etc.).
* **Submission History:** Review all past submissions for any problem, and view the submitted code.
* **Modern UI:** A sleek, resizable, and responsive interface with a dark/light theme toggle.

### For Admins
* **Problem Management:** A secure admin panel to create, read, update, and delete problems.
* **Hidden Test Cases:** Add and manage hidden test cases for robust grading.
* **Role-Based Access:** Secure admin routes are only accessible to users with the 'admin' role.

### AI-Powered Assistance (via Google Gemini)
* **Explain Problem:** Get a clear, beginner-friendly explanation of the problem statement.
* **Debug Wrong Code:** After a failed submission, ask the AI to explain what's wrong with your logic.
* **Code Review:** Get an expert review of your code's efficiency, style, and correctness.

## 💻 Tech Stack

* **Frontend:** React (Vite), Tailwind CSS, shadcn/ui, Monaco Editor, Axios
* **Backend (API Server):** Node.js, Express, Mongoose, MongoDB
* **Code Runner (Execution Engine):** Node.js, Express, Docker
* **Authentication:** JSON Web Tokens (JWT) with HTTP-Only Cookies
* **AI:** Google Gemini API

## 🏗️ Architecture

This project is built on a microservice-oriented architecture to ensure security and scalability:

1.  **`client`:** A modern React single-page application that serves as the user interface.
2.  **`backend`:** The main API server that handles user authentication, problem data, submissions, and communication with the AI.
3.  **`runner`:** A completely isolated service that securely executes user-submitted code inside Docker containers. It receives code from the backend, runs it, and returns the result.

## 🚀 Getting Started

### Prerequisites
* Node.js (v18 or later)
* npm
* Docker Desktop
* Git

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

2.  **Backend Setup:**
    ```bash
    cd backend
    npm install
    # Create a .env file and add your variables (see below)
    node index.js
    ```

3.  **Runner Setup:**
    * (In a new terminal)
    ```bash
    cd runner
    npm install
    # Build the base Docker images (only needs to be done once)
    node build_images.js
    # Start the runner server
    node index.js
    ```

4.  **Client Setup:**
    * (In a third terminal)
    ```bash
    cd client
    npm install
    npm run dev
    ```

The application will be available at `http://localhost:5173`.

## ⚙️ Environment Variables

You will need to create a `.env` file in the `backend` directory with the following variables:

```env
# backend/.env

# Your MongoDB connection string
MONGO_URI=mongodb+srv://...

# A secret key for signing JWTs
JWT_SECRET=yoursupersecretkey

# Your Google Gemini API Key
GEMINI_API_KEY=your key
