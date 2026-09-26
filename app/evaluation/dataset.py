"""20-Item Evaluation Benchmark Dataset for SkillPilot (Phase 10)."""
from typing import List
from app.models.schemas import EvaluationItem

BENCHMARK_DATASET: List[EvaluationItem] = [
    # -------------------------------------------------------------------------
    # Category 1: Code Analysis (Single Skill)
    # -------------------------------------------------------------------------
    EvaluationItem(
        id=1,
        category="code_analysis",
        query="Analyze this Python code for bugs and mutable default argument issues.",
        code="""def process_items(data=[]):
    data.append(1)
    return data
""",
        expected_skill="code_analysis",
        expected_chain=["code_analysis"],
        is_negative=False,
        description="Detection of Python mutable default argument bug",
    ),
    EvaluationItem(
        id=2,
        category="code_analysis",
        query="Analyze this Java code for bugs and thread safety hazards.",
        code="""public class UserManager {
    private List<String> users = new ArrayList<>();
    public void addUser(String user) {
        users.add(user);
    }
}""",
        expected_skill="code_analysis",
        expected_chain=["code_analysis"],
        is_negative=False,
        description="Static analysis of Java class with non-thread-safe collection",
    ),
    EvaluationItem(
        id=3,
        category="code_analysis",
        query="Find all bugs and inefficiencies in this loop implementation.",
        code="""def sum_even(numbers):
    total = 0
    for i in range(len(numbers)):
        if numbers[i] == True:
            total += 1
    return total
""",
        expected_skill="code_analysis",
        expected_chain=["code_analysis"],
        is_negative=False,
        description="Detection of range(len(...)) and boolean comparison anti-patterns",
    ),

    # -------------------------------------------------------------------------
    # Category 2: Security Analysis (Single Skill)
    # -------------------------------------------------------------------------
    EvaluationItem(
        id=4,
        category="security_analysis",
        query="Find vulnerabilities, injection flaws, and exposed credentials in this API.",
        code="""import os
API_KEY = "sk_live_secret_token_123456"
def execute_cmd(user_cmd):
    os.system(user_cmd)
""",
        expected_skill="security_analysis",
        expected_chain=["security_analysis"],
        is_negative=False,
        description="Detection of hardcoded secret key and command injection vulnerability",
    ),
    EvaluationItem(
        id=5,
        category="security_analysis",
        query="Perform a security analysis on this authentication controller.",
        code="""def authenticate(username, password):
    query = f"SELECT * FROM users WHERE user='{username}' AND pass='{password}'"
    return db.execute(query)
""",
        expected_skill="security_analysis",
        expected_chain=["security_analysis"],
        is_negative=False,
        description="Identification of severe SQL injection via f-string query formatting",
    ),
    EvaluationItem(
        id=6,
        category="security_analysis",
        query="Check this configuration for security weaknesses and secret leaks.",
        code="""DEBUG = True
SECRET_KEY = "production_super_secret_jwt_key_999"
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
""",
        expected_skill="security_analysis",
        expected_chain=["security_analysis"],
        is_negative=False,
        description="Evaluation of wildcard CORS, debug mode, and exposed production secrets",
    ),

    # -------------------------------------------------------------------------
    # Category 3: Documentation (Single Skill)
    # -------------------------------------------------------------------------
    EvaluationItem(
        id=7,
        category="documentation",
        query="Create a README and technical documentation for this repository.",
        code="""SkillPilot runtime supporting dynamic markdown skill execution and stateful memory.""",
        expected_skill="documentation",
        expected_chain=["documentation"],
        is_negative=False,
        description="README generation containing architecture, setup, and features",
    ),
    EvaluationItem(
        id=8,
        category="documentation",
        query="Generate comprehensive API documentation for these endpoints.",
        code="""@app.post("/agent/run")
def run_agent(request: ChatRequest) -> ChatResponse:
    return agent.run(request.query)
""",
        expected_skill="documentation",
        expected_chain=["documentation"],
        is_negative=False,
        description="API endpoint technical reference with inputs, outputs, and status codes",
    ),
    EvaluationItem(
        id=9,
        category="documentation",
        query="Document the setup instructions, architecture, and usage for this service.",
        code="""FastAPI autonomous agent using LangGraph state machine and OpenRouter LLM.""",
        expected_skill="documentation",
        expected_chain=["documentation"],
        is_negative=False,
        description="Developer onboarding guide with environment setup and execution steps",
    ),

    # -------------------------------------------------------------------------
    # Category 4: Code Explanation (Single Skill)
    # -------------------------------------------------------------------------
    EvaluationItem(
        id=10,
        category="code_explanation",
        query="Explain this Java code and tell me how it works line by line.",
        code="""public class Factorial {
    public static int compute(int n) {
        return (n <= 1) ? 1 : n * compute(n - 1);
    }
}""",
        expected_skill="code_explanation",
        expected_chain=["code_explanation"],
        is_negative=False,
        description="Line-by-line explanation of recursive Java method",
    ),
    EvaluationItem(
        id=11,
        category="code_explanation",
        query="What does this complex recursive function do? Walk me through it.",
        code="""def fibonacci_stream():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b
""",
        expected_skill="code_explanation",
        expected_chain=["code_explanation"],
        is_negative=False,
        description="Conceptual explanation of Python infinite generator stream",
    ),
    EvaluationItem(
        id=12,
        category="code_explanation",
        query="Explain the architecture and mechanism of this asynchronous handler.",
        code="""async def handle_stream(websocket, queue):
    async for message in websocket:
        await queue.put(message)
""",
        expected_skill="code_explanation",
        expected_chain=["code_explanation"],
        is_negative=False,
        description="Step-by-step breakdown of async event queue processing",
    ),

    # -------------------------------------------------------------------------
    # Category 5: Task Planning (Single Skill)
    # -------------------------------------------------------------------------
    EvaluationItem(
        id=13,
        category="task_planning",
        query="Give me a roadmap and implementation plan for building a payment microservice.",
        code=None,
        expected_skill="task_planning",
        expected_chain=["task_planning"],
        is_negative=False,
        description="Phased implementation roadmap for distributed payment processing",
    ),
    EvaluationItem(
        id=14,
        category="task_planning",
        query="Break down the development tasks and dependencies for migrating our database.",
        code=None,
        expected_skill="task_planning",
        expected_chain=["task_planning"],
        is_negative=False,
        description="Database schema migration phases, dependencies, and rollout strategy",
    ),
    EvaluationItem(
        id=15,
        category="task_planning",
        query="Outline the phases, architecture, and testing strategy for building a chat application.",
        code=None,
        expected_skill="task_planning",
        expected_chain=["task_planning"],
        is_negative=False,
        description="Architecture phases, WebSockets integration, and testing plan",
    ),

    # -------------------------------------------------------------------------
    # Category 6: Multi-Skill Chaining (Multi-Step Workflows)
    # -------------------------------------------------------------------------
    EvaluationItem(
        id=16,
        category="multi_skill_chaining",
        query="Analyze this Python API for security issues and then create documentation explaining the vulnerabilities.",
        code="""import os
API_KEY = "sk_live_secret_key"
def run(cmd):
    os.system(cmd)
""",
        expected_skill="security_analysis",
        expected_chain=["security_analysis", "documentation"],
        is_negative=False,
        description="2-step sequential workflow: security audit followed by remediation documentation",
    ),
    EvaluationItem(
        id=17,
        category="multi_skill_chaining",
        query="Review this code for bugs, then analyze security vulnerabilities, after that generate documentation.",
        code="""import os
API_KEY = "secret_123"
def bad(items=[]):
    os.system(f"echo {items}")
""",
        expected_skill="code_analysis",
        expected_chain=["code_analysis", "security_analysis", "documentation"],
        is_negative=False,
        description="3-step sequential workflow: code quality -> security audit -> technical documentation",
    ),

    # -------------------------------------------------------------------------
    # Category 7: Invalid / Off-Domain Requests (Negative Controls)
    # -------------------------------------------------------------------------
    EvaluationItem(
        id=18,
        category="invalid_request",
        query="Tell me a funny joke about programming.",
        code=None,
        expected_skill=None,
        expected_chain=[],
        is_negative=True,
        description="Negative control: off-domain joke query must be rejected with No matching skill",
    ),
    EvaluationItem(
        id=19,
        category="invalid_request",
        query="What is the weather forecast for New York City tomorrow?",
        code=None,
        expected_skill=None,
        expected_chain=[],
        is_negative=True,
        description="Negative control: weather forecast query must be rejected with No matching skill",
    ),
    EvaluationItem(
        id=20,
        category="invalid_request",
        query="Can you give me a recipe for authentic Neapolitan pizza?",
        code=None,
        expected_skill=None,
        expected_chain=[],
        is_negative=True,
        description="Negative control: culinary recipe request must be rejected with No matching skill",
    ),
]


def get_benchmark_dataset() -> List[EvaluationItem]:
    """Returns the immutable 20-item evaluation benchmark suite."""
    return list(BENCHMARK_DATASET)
