#!/bin/bash
# AI Debate Arena Test Runner
# "I'm learnding!" - Ralph Wiggum

echo "🎭 AI Debate Arena Test Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo '"Me fail tests? Thats unpossible!" - Ralph Wiggum'
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio pytest-cov
fi

# Parse arguments
COVERAGE=false
E2E=false
VERBOSE=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --coverage|-c) COVERAGE=true ;;
        --e2e|-e) E2E=true ;;
        --verbose|-v) VERBOSE=true ;;
        --all|-a) COVERAGE=true; E2E=true ;;
        --help|-h)
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --coverage, -c    Run with coverage report"
            echo "  --e2e, -e         Include E2E tests (requires playwright)"
            echo "  --verbose, -v     Verbose output"
            echo "  --all, -a         Run all tests with coverage"
            echo "  --help, -h        Show this help"
            echo ""
            echo '"I bent my Wookie!" - Ralph Wiggum'
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# Build pytest command
PYTEST_CMD="pytest"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-report=html --cov-report=term-missing"
fi

if [ "$E2E" = false ]; then
    PYTEST_CMD="$PYTEST_CMD --ignore=tests/e2e"
fi

echo -e "${YELLOW}🧪 Running: $PYTEST_CMD${NC}"
echo ""

# Run tests
$PYTEST_CMD

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo '"I\'m learnding!" - Ralph Wiggum'
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    echo '"It tastes like burning!" - Ralph Wiggum'
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $EXIT_CODE