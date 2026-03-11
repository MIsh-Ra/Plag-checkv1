#!/bin/bash

# Configuration
TEST_DIR="tests/system"
LOG_DIR="tests/logs"
LOG_FILE="$LOG_DIR/test_execution_$(date +%Y%m%d_%H%M%S).log"

# Ensure directories exist
mkdir -p "$LOG_DIR"

echo "=========================================" | tee -a "$LOG_FILE"
echo "Starting Alethian System Tests" | tee -a "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "=========================================" | tee -a "$LOG_FILE"

# Activate virtual environment if present
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
fi

# Determine phase to run
PHASE=$1
if [ -z "$PHASE" ]; then
    TARGET="$TEST_DIR"
else
    TARGET="$TEST_DIR/$PHASE"
fi

echo "Running tests in: $TARGET" | tee -a "$LOG_FILE"

# Run pytest with logging
# We need to explicitly set PYTHONPATH to point to backend source
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend

pytest "$TARGET" -v --log-cli-level=INFO | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

echo "=========================================" | tee -a "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ]; then
    echo "Tests PASSED" | tee -a "$LOG_FILE"
else
    echo "Tests FAILED" | tee -a "$LOG_FILE"
fi
echo "Log saved to: $LOG_FILE"
echo "=========================================" | tee -a "$LOG_FILE"

exit $EXIT_CODE
