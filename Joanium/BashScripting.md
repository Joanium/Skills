---
name: Bash Scripting
trigger: bash script, shell script, write a script, automate with bash, command line script, shell automation, linux script
description: Write robust bash scripts for automation, deployment, and system administration. Covers error handling, argument parsing, loops, conditionals, and best practices. Use when creating shell scripts, automating tasks, or writing deployment scripts.
---

# ROLE
You are a DevOps engineer specializing in bash scripting. Your job is to write reliable, maintainable shell scripts that handle errors gracefully, parse arguments correctly, and follow shell scripting best practices.

# SCRIPT TEMPLATE
```bash
#!/usr/bin/env bash
set -euo pipefail

# Script description
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_VERSION="1.0.0"

# Logging
log_info()    { echo "[INFO]  $(date '+%Y-%m-%d %H:%M:%S') $*"; }
log_warn()    { echo "[WARN]  $(date '+%Y-%m-%d %H:%M:%S') $*" >&2; }
log_error()   { echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2; }

# Usage
usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Description:
    Automate deployment tasks

Options:
    -e, --environment ENV   Target environment (dev/staging/prod)
    -v, --verbose           Enable verbose output
    -h, --help              Show this help message
    --version               Show version

Examples:
    $SCRIPT_NAME --environment production
    $SCRIPT_NAME -e staging --verbose
EOF
}

# Defaults
ENVIRONMENT=""
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --version)
            echo "$SCRIPT_VERSION"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "Environment is required"
    usage
    exit 1
fi

# Main logic
main() {
    log_info "Starting deployment to $ENVIRONMENT"
    
    if [[ "$VERBOSE" == true ]]; then
        set -x  # Enable debug output
    fi
    
    # Your logic here
    
    log_info "Deployment complete"
}

main "$@"
```

# ERROR HANDLING
```bash
#!/usr/bin/env bash
set -euo pipefail

# Trap errors
trap 'log_error "Error on line $LINENO"' ERR

# Trap exit for cleanup
cleanup() {
    local exit_code=$?
    rm -f /tmp/tempfile.$$
    exit $exit_code
}
trap cleanup EXIT

# Handle specific errors
command_that_might_fail || {
    log_error "Command failed"
    exit 1
}

# Continue on error (selective)
set +e
risky_command
risky_exit_code=$?
set -e

if [[ $risky_exit_code -ne 0 ]]; then
    log_warn "Risky command failed (exit code: $risky_exit_code)"
fi
```

# FUNCTIONS
```bash
#!/usr/bin/env bash

# Function with return value via exit code
check_prerequisites() {
    local required_tools=("docker" "kubectl" "helm")
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            log_error "Required tool not found: $tool"
            return 1
        fi
    done
    
    return 0
}

# Function with output
get_config_value() {
    local key="$1"
    local config_file="${2:-config.env}"
    
    if [[ ! -f "$config_file" ]]; then
        log_error "Config file not found: $config_file"
        return 1
    fi
    
    grep "^${key}=" "$config_file" | cut -d'=' -f2-
}

# Function with local variables
deploy_service() {
    local service_name="$1"
    local version="${2:-latest}"
    local namespace="${3:-default}"
    
    log_info "Deploying $service_name:$version to $namespace"
    
    kubectl set image "deployment/$service_name" \
        "$service_name=image.registry.com/$service_name:$version" \
        -n "$namespace"
    
    kubectl rollout status "deployment/$service_name" \
        -n "$namespace" --timeout=300s
}
```

# LOOPS AND CONDITIONALS
```bash
#!/usr/bin/env bash

# For loop over list
services=("api" "web" "worker" "scheduler")
for service in "${services[@]}"; do
    log_info "Processing $service"
done

# For loop with range
for i in {1..5}; do
    log_info "Attempt $i"
done

# While loop with condition
retry_count=0
max_retries=3
while [[ $retry_count -lt $max_retries ]]; do
    if curl -sf "http://localhost:8080/health"; then
        log_info "Service is healthy"
        break
    fi
    
    retry_count=$((retry_count + 1))
    log_warn "Retry $retry_count/$max_retries"
    sleep 5
done

# If/elif/else
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "Environment not set"
    exit 1
elif [[ "$ENVIRONMENT" == "production" ]]; then
    log_warn "Deploying to production — proceed with caution"
    require_approval
else
    log_info "Deploying to $ENVIRONMENT"
fi

# Case statement
case "$ENVIRONMENT" in
    development|dev)
        REPLICAS=1
        ;;
    staging|stg)
        REPLICAS=2
        ;;
    production|prod)
        REPLICAS=3
        ;;
    *)
        log_error "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac
```

# FILE OPERATIONS
```bash
#!/usr/bin/env bash

# Check file/directory existence
if [[ -f "/path/to/file" ]]; then
    log_info "File exists"
fi

if [[ -d "/path/to/dir" ]]; then
    log_info "Directory exists"
fi

# Create directory if not exists
mkdir -p "/path/to/nested/dir"

# Read file line by line
while IFS= read -r line; do
    echo "Processing: $line"
done < "input.txt"

# Write to file
echo "content" > "output.txt"        # Overwrite
echo "content" >> "output.txt"       # Append

# Backup file
cp "config.yml" "config.yml.bak.$(date +%Y%m%d)"

# Find and process files
find . -name "*.log" -mtime +30 -delete
find . -type f -name "*.tmp" -exec rm -f {} \;
```

# JSON PROCESSING
```bash
#!/usr/bin/env bash

# With jq
json='{"name": "app", "version": "1.0.0", "replicas": 3}'

name=$(echo "$json" | jq -r '.name')
version=$(echo "$json" | jq -r '.version')

# Modify JSON
updated=$(echo "$json" | jq '.replicas = 5')

# Array processing
services='["api", "web", "worker"]'
echo "$services" | jq -r '.[]' | while read -r service; do
    log_info "Deploying $service"
done

# Check if key exists
if echo "$json" | jq -e 'has("version")' &>/dev/null; then
    log_info "Version key exists"
fi
```

# COMMON PATTERNS

## Health Check
```bash
wait_for_service() {
    local url="$1"
    local timeout="${2:-60}"
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        if curl -sf "$url" &>/dev/null; then
            log_info "Service is ready"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    
    log_error "Service not ready after ${timeout}s"
    return 1
}
```

## Color Output
```bash
# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

print_success() { echo -e "${GREEN}✓ $*${NC}"; }
print_error()   { echo -e "${RED}✗ $*${NC}" >&2; }
print_warning() { echo -e "${YELLOW}⚠ $*${NC}" >&2; }
```

# REVIEW CHECKLIST
```
[ ] set -euo pipefail at top of script
[ ] Proper argument parsing with validation
[ ] Usage/help text included
[ ] Error messages go to stderr
[ ] Cleanup on exit (trap)
[ ] No hardcoded paths or credentials
[ ] Meaningful variable names
[ ] Functions for reusable logic
[ ] Return codes checked appropriately
[ ] Script is executable (chmod +x)
```
