#!/bin/bash
# Registry 자동 갱신 스크립트
# PostToolUse hook에서 호출됨

# stdin에서 JSON 읽기
INPUT=$(cat)

# file_path 추출
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

# templates/contents/**/template.yaml 패턴 확인
if echo "$FILE_PATH" | grep -q 'templates/contents/.*/template\.yaml$'; then
    cd /home/jji/project/ppt-gen
    python -c "
import sys
sys.path.insert(0, '.claude/skills/ppt-extract/scripts')
from registry_manager import RegistryManager
RegistryManager().rebuild_all()
" 2>/dev/null
    echo '{"systemMessage": "✅ Registry 자동 갱신 완료"}'
fi

exit 0
