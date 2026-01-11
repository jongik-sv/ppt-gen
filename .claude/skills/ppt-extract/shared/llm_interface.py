#!/usr/bin/env python3
"""
LLM Interface.

Claude API를 호출하여 슬롯 분류, 레이아웃 분류 등을 자동화합니다.

사용 방법:
    1. 환경변수 ANTHROPIC_API_KEY 설정
    2. from shared.llm_interface import ClaudeLLM
    3. llm = ClaudeLLM()
    4. result = llm.classify_slots(shapes_info)
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 스크립트 디렉토리를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))


# Anthropic API 모델
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class LLMError(Exception):
    """LLM 호출 오류."""
    pass


class ClaudeLLM:
    """Claude API 호출 인터페이스."""

    def __init__(self, model: str = DEFAULT_MODEL, use_cli: bool = True):
        """
        Args:
            model: Claude 모델 ID
            use_cli: True면 Claude CLI 사용, False면 API 직접 호출
        """
        self.model = model
        self.use_cli = use_cli
        self._api_key = os.environ.get('ANTHROPIC_API_KEY')

        # CLI 사용 가능 여부 확인
        if use_cli:
            self._check_cli_available()

    def _check_cli_available(self) -> bool:
        """Claude CLI 사용 가능 여부 확인."""
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def classify_slots(
        self,
        shapes_info: List[Dict],
        context: Optional[str] = None
    ) -> Dict:
        """
        도형 정보를 분석하여 슬롯 분류.

        Args:
            shapes_info: 도형 정보 목록
                [{'id': 'shape-1', 'type': 'text', 'text': '제목', 'position': {...}}, ...]
            context: 추가 컨텍스트 (카테고리 힌트 등)

        Returns:
            분류 결과:
            {
                'slots': [
                    {'name': 'title', 'type': 'text', 'shape_ids': ['shape-1']},
                    {'name': 'items', 'type': 'array', 'shape_ids': ['shape-2', 'shape-3']}
                ]
            }
        """
        prompt = self._build_slot_prompt(shapes_info, context)
        response = self._call(prompt)
        return self._parse_json_response(response)

    def classify_layouts(
        self,
        layouts_info: List[Dict],
        context: Optional[str] = None
    ) -> Dict:
        """
        레이아웃 정보를 분석하여 타입 분류.

        Args:
            layouts_info: 레이아웃 정보 목록
                [{'name': 'Layout 1', 'placeholders': [...], 'thumbnail': '...'}, ...]
            context: 추가 컨텍스트

        Returns:
            분류 결과:
            {
                'layouts': [
                    {'name': 'Layout 1', 'type': 'cover'},
                    {'name': 'Layout 2', 'type': 'body'}
                ]
            }
        """
        prompt = self._build_layout_prompt(layouts_info, context)
        response = self._call(prompt)
        return self._parse_json_response(response)

    def analyze_content(
        self,
        shapes_info: List[Dict],
        task: str = "describe"
    ) -> str:
        """
        콘텐츠 분석.

        Args:
            shapes_info: 도형 정보
            task: 작업 유형 (describe, categorize, suggest)

        Returns:
            분석 결과 텍스트
        """
        prompt = self._build_analysis_prompt(shapes_info, task)
        return self._call(prompt)

    def _build_slot_prompt(
        self,
        shapes_info: List[Dict],
        context: Optional[str] = None
    ) -> str:
        """슬롯 분류 프롬프트 생성."""
        shapes_json = json.dumps(shapes_info, ensure_ascii=False, indent=2)

        prompt = f"""당신은 PowerPoint 슬라이드 구조 분석 전문가입니다.

다음 도형 정보를 분석하여 재사용 가능한 슬롯(placeholder)으로 분류해주세요.

## 도형 정보
```json
{shapes_json}
```

{f"## 컨텍스트\n{context}" if context else ""}

## 분류 규칙
1. **title**: 상단에 위치한 큰 텍스트 (보통 y < 25%)
2. **subtitle**: 제목 아래의 보조 텍스트
3. **items**: 반복되는 패턴의 텍스트/이미지 그룹
4. **image**: 단일 이미지
5. **images**: 복수 이미지 배열
6. **text_N**: 기타 텍스트 (N은 순번)

## 출력 형식 (JSON)
```json
{{
  "slots": [
    {{"name": "title", "type": "text", "shape_ids": ["shape-1"], "required": true}},
    {{"name": "items", "type": "array", "shape_ids": ["shape-2", "shape-3"], "item_schema": [{{"name": "text", "type": "text"}}]}}
  ]
}}
```

JSON만 출력하세요."""

        return prompt

    def _build_layout_prompt(
        self,
        layouts_info: List[Dict],
        context: Optional[str] = None
    ) -> str:
        """레이아웃 분류 프롬프트 생성."""
        layouts_json = json.dumps(layouts_info, ensure_ascii=False, indent=2)

        prompt = f"""당신은 PowerPoint 레이아웃 분류 전문가입니다.

다음 슬라이드 레이아웃 정보를 분석하여 타입을 분류해주세요.

## 레이아웃 정보
```json
{layouts_json}
```

{f"## 컨텍스트\n{context}" if context else ""}

## 분류 기준
- **cover**: 표지 (로고, 대제목, 회사명)
- **toc**: 목차 (번호 목록)
- **section**: 섹션 구분 (큰 텍스트만)
- **body**: 일반 내지 (제목 + 콘텐츠)
- **closing**: 마무리 (감사, 연락처)

## 출력 형식 (JSON)
```json
{{
  "layouts": [
    {{"name": "Layout 1", "type": "cover", "confidence": 0.9}},
    {{"name": "Layout 2", "type": "body", "confidence": 0.8}}
  ]
}}
```

JSON만 출력하세요."""

        return prompt

    def _build_analysis_prompt(
        self,
        shapes_info: List[Dict],
        task: str
    ) -> str:
        """콘텐츠 분석 프롬프트 생성."""
        shapes_json = json.dumps(shapes_info, ensure_ascii=False, indent=2)

        task_instructions = {
            'describe': "이 슬라이드의 목적과 구조를 간단히 설명해주세요.",
            'categorize': "이 슬라이드의 카테고리를 분류해주세요. (grid, list, timeline, chart 등)",
            'suggest': "이 슬라이드를 개선할 수 있는 방법을 제안해주세요."
        }

        instruction = task_instructions.get(task, task_instructions['describe'])

        return f"""## 도형 정보
```json
{shapes_json}
```

## 작업
{instruction}"""

    def _call(self, prompt: str) -> str:
        """
        Claude API 호출.

        Args:
            prompt: 프롬프트

        Returns:
            응답 텍스트

        Raises:
            LLMError: 호출 실패 시
        """
        if self.use_cli:
            return self._call_cli(prompt)
        else:
            return self._call_api(prompt)

    def _call_cli(self, prompt: str) -> str:
        """Claude CLI 호출."""
        try:
            # claude -p "prompt" --output-format text
            result = subprocess.run(
                ['claude', '-p', prompt, '--output-format', 'text'],
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8'
            )

            if result.returncode != 0:
                raise LLMError(f"Claude CLI 오류: {result.stderr}")

            return result.stdout.strip()

        except FileNotFoundError:
            raise LLMError("Claude CLI가 설치되어 있지 않습니다. 'npm install -g @anthropics/claude-code' 실행 필요")
        except subprocess.TimeoutExpired:
            raise LLMError("Claude CLI 응답 시간 초과 (60초)")

    def _call_api(self, prompt: str) -> str:
        """Anthropic API 직접 호출."""
        if not self._api_key:
            raise LLMError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")

        try:
            import anthropic
        except ImportError:
            raise LLMError("anthropic 패키지가 설치되어 있지 않습니다. 'pip install anthropic' 실행 필요")

        try:
            client = anthropic.Anthropic(api_key=self._api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text

        except anthropic.APIError as e:
            raise LLMError(f"Anthropic API 오류: {e}")

    def _parse_json_response(self, response: str) -> Dict:
        """
        JSON 응답 파싱.

        Args:
            response: LLM 응답 텍스트

        Returns:
            파싱된 JSON 객체

        Raises:
            LLMError: JSON 파싱 실패 시
        """
        # 코드 블록 제거
        if '```json' in response:
            start = response.find('```json') + 7
            end = response.find('```', start)
            response = response[start:end]
        elif '```' in response:
            start = response.find('```') + 3
            end = response.find('```', start)
            response = response[start:end]

        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise LLMError(f"JSON 파싱 실패: {e}\n응답: {response[:200]}")


def main():
    """테스트용 CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM 인터페이스 테스트")
    parser.add_argument('--test', choices=['slots', 'layouts', 'analyze'], default='slots')
    parser.add_argument('--use-api', action='store_true', help='API 직접 호출 사용')

    args = parser.parse_args()

    llm = ClaudeLLM(use_cli=not args.use_api)

    if args.test == 'slots':
        # 테스트 도형 데이터
        shapes = [
            {'id': 'shape-1', 'type': 'text', 'text': '월별 매출 현황', 'position': {'x': 5, 'y': 5}},
            {'id': 'shape-2', 'type': 'text', 'text': '1월: 100만원', 'position': {'x': 10, 'y': 30}},
            {'id': 'shape-3', 'type': 'text', 'text': '2월: 120만원', 'position': {'x': 10, 'y': 40}},
            {'id': 'shape-4', 'type': 'text', 'text': '3월: 150만원', 'position': {'x': 10, 'y': 50}},
        ]
        result = llm.classify_slots(shapes)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.test == 'layouts':
        layouts = [
            {'name': 'Title Slide', 'placeholders': ['title', 'subtitle', 'logo']},
            {'name': 'Content Layout', 'placeholders': ['title', 'body']},
        ]
        result = llm.classify_layouts(layouts)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.test == 'analyze':
        shapes = [
            {'id': 'shape-1', 'type': 'text', 'text': '팀 소개'},
            {'id': 'shape-2', 'type': 'image', 'position': {'x': 10, 'y': 30}},
            {'id': 'shape-3', 'type': 'image', 'position': {'x': 40, 'y': 30}},
            {'id': 'shape-4', 'type': 'image', 'position': {'x': 70, 'y': 30}},
        ]
        result = llm.analyze_content(shapes, task='categorize')
        print(result)


if __name__ == "__main__":
    main()
