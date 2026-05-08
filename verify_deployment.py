#!/usr/bin/env python3
"""
Pre-deployment verification script

Checks that all requirements are met before deploying to production.
"""
import os
import sys
import subprocess
from pathlib import Path


class Colors:
    """Terminal colors"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def check_file_exists(filepath, required=True):
    """Check if file exists"""
    if Path(filepath).exists():
        print_success(f"Found: {filepath}")
        return True
    else:
        if required:
            print_error(f"Missing required file: {filepath}")
        else:
            print_warning(f"Optional file not found: {filepath}")
        return False


def check_env_file():
    """Check .env file configuration"""
    print_header("Environment Configuration")
    
    env_example_exists = check_file_exists(".env.example", required=True)
    env_exists = check_file_exists(".env", required=False)
    
    if not env_exists:
        print_warning(".env file not found. Create from .env.example for local testing")
    
    # Check for sensitive data in git
    gitignore_exists = check_file_exists(".gitignore", required=True)
    if gitignore_exists:
        with open(".gitignore") as f:
            gitignore_content = f.read()
            if ".env" in gitignore_content:
                print_success(".env is in .gitignore")
            else:
                print_error(".env NOT in .gitignore! Add it immediately!")
    
    return env_example_exists


def check_dependencies():
    """Check Python dependencies"""
    print_header("Dependencies Check")
    
    # Check requirements.txt
    req_exists = check_file_exists("requirements.txt", required=True)
    
    if req_exists:
        # Try to install dependencies (dry run)
        try:
            result = subprocess.run(
                ["pip", "check"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print_success("All dependencies are compatible")
            else:
                print_warning("Dependency conflicts detected:")
                print(result.stdout)
        except Exception as e:
            print_warning(f"Could not verify dependencies: {e}")
    
    return req_exists


def check_deployment_files():
    """Check deployment configuration files"""
    print_header("Deployment Files")
    
    files = {
        "Procfile": "Render/Railway startup",
        "Dockerfile": "Docker deployment",
        "render.yaml": "Render configuration",
        "railway.json": "Railway configuration",
        ".dockerignore": "Docker build optimization"
    }
    
    all_exist = True
    for filename, description in files.items():
        exists = check_file_exists(filename, required=False)
        if not exists:
            all_exist = False
            print_warning(f"{filename} ({description}) not found")
    
    return all_exist


def check_documentation():
    """Check documentation files"""
    print_header("Documentation")
    
    docs = {
        "README-DEPLOYMENT.md": "Deployment guide",
    }
    
    docs_exist = True
    for filename, description in docs.items():
        if not check_file_exists(filename, required=False):
            docs_exist = False
    
    return docs_exist


def check_tests():
    """Check if tests exist and pass"""
    print_header("Tests")
    
    # Check test files
    test_files = [
        "test_endpoints.py",
        "test_agent_workflow.py",
        "test_error_handling.py"
    ]
    
    tests_exist = all(check_file_exists(f, required=False) for f in test_files)
    
    if tests_exist:
        print("\nRunning tests...")
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "test_endpoints.py", "test_agent_workflow.py", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print_success("All tests passed!")
            else:
                print_error("Some tests failed. Fix before deploying!")
                print(result.stdout[-500:])  # Last 500 chars
                return False
        except subprocess.TimeoutExpired:
            print_warning("Tests timed out")
            return False
        except Exception as e:
            print_warning(f"Could not run tests: {e}")
            return False
    
    return tests_exist


def check_security():
    """Check security configurations"""
    print_header("Security Checks")
    
    issues = []
    
    # Check for hardcoded secrets
    print("Scanning for potential secrets...")
    
    patterns = [
        ("sk-", "OpenAI API key pattern"),
        ("password=\"", "Password in code"),
        ("secret=\"", "Secret in code"),
    ]
    
    # Patterns that are OK (environment variable usage)
    safe_patterns = [
        "os.getenv",
        "os.environ",
        "getenv(",
        "your_",
        ".env",
        "ENV"
    ]
    
    for root, dirs, files in os.walk("."):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'node_modules', '.pytest_cache']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for pattern, description in patterns:
                        if pattern in content:
                            # Check if it's a safe usage
                            is_safe = any(safe in content for safe in safe_patterns)
                            if not is_safe:
                                issues.append(f"{filepath}: Potential {description}")
    
    if issues:
        print_error("Potential security issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print_success("No obvious security issues found")
    
    return len(issues) == 0


def check_app_structure():
    """Check application structure"""
    print_header("Application Structure")
    
    required_dirs = ["app", "app/routes", "app/services", "app/tools", "app/agents", "app/utils"]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).is_dir():
            print_success(f"Directory exists: {directory}")
        else:
            print_error(f"Missing directory: {directory}")
            all_exist = False
    
    # Check main.py
    main_exists = check_file_exists("app/main.py", required=True)
    
    return all_exist and main_exists


def main():
    """Run all checks"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("🚀 Pre-Deployment Verification")
    print(f"{'='*60}{Colors.END}\n")
    
    checks = [
        ("Application Structure", check_app_structure),
        ("Environment Files", check_env_file),
        ("Dependencies", check_dependencies),
        ("Deployment Files", check_deployment_files),
        ("Documentation", check_documentation),
        ("Tests", check_tests),
        ("Security", check_security)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Error during {name} check: {e}")
            results[name] = False
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        if result:
            print_success(f"{name}: PASS")
        else:
            print_error(f"{name}: FAIL")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} checks passed{Colors.END}\n")
    
    if passed == total:
        print_success("✓ All checks passed! Ready for deployment.\n")
        return 0
    else:
        print_warning("⚠ Some checks failed. Please fix issues before deploying.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
