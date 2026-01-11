#!/usr/bin/env python3
"""
Image Content Extractor.

이미지(PNG/JPG)에서 콘텐츠 템플릿을 추출합니다.
Claude Code 대화에서 분석한 슬롯 정보를 받아 YAML + HTML 생성.
(OOXML은 이미지에서 복원 불가)
"""

import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 스크립트 디렉토리를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared.yaml_utils import save_yaml


@dataclass
class SlotInfo:
    """슬롯 정보 (Claude Code가 전달)."""
    name: str
    type: str  # text, image, array
    required: bool = True
    position: Dict[str, float] = field(default_factory=dict)  # x, y, width, height (%)
    example: Optional[str] = None
    item_schema: Optional[List[Dict]] = None
    count: Optional[int] = None  # array 타입일 때 요소 수


@dataclass
class ImageContentTemplate:
    """이미지 기반 콘텐츠 템플릿."""
    id: str
    category: str
    pattern: str
    slots: List[SlotInfo]
    semantic_description: str
    match_keywords: List[str]
    source_type: str = 'image'  # 항상 'image'
    source_file: Optional[str] = None
    has_ooxml: bool = False  # 항상 False
    output_path: Optional[Path] = None


class ImageContentExtractor:
    """이미지 콘텐츠 추출기.

    이미지 파일과 Claude Code가 분석한 슬롯 정보를 받아
    콘텐츠 템플릿을 생성합니다.

    Usage:
        extractor = ImageContentExtractor(
            input_path=Path("design.png"),
            slots_data={
                "category": "grid",
                "pattern": "grid-3col",
                "semantic_description": "3열 카드 그리드",
                "slots": [
                    {"name": "title", "type": "text"},
                    {"name": "items", "type": "array", "count": 3}
                ],
                "keywords": ["그리드", "카드"]
            }
        )
        templates = extractor.run()
    """

    def __init__(
        self,
        input_path: Path,
        slots_data: Dict,
        category: Optional[str] = None,
        output_path: Optional[Path] = None,
        template_name: Optional[str] = None
    ):
        """
        Args:
            input_path: 입력 이미지 경로
            slots_data: Claude Code가 분석한 슬롯 데이터
                {
                    "category": "grid",
                    "pattern": "grid-3col-cards",
                    "semantic_description": "상단 제목과 3개 카드 그리드",
                    "slots": [
                        {"name": "title", "type": "text", "position": {...}},
                        {"name": "items", "type": "array", "count": 3, ...}
                    ],
                    "keywords": ["그리드", "카드", "3열"]
                }
            category: 카테고리 (slots_data에서 추출 가능)
            output_path: 출력 경로
            template_name: 템플릿 이름
        """
        self.input_path = Path(input_path)
        self.slots_data = slots_data
        self.category = category or slots_data.get('category', 'body')
        self.output_path = output_path
        self.template_name = template_name

    def run(self) -> List[ImageContentTemplate]:
        """추출 실행."""
        print(f"\n이미지 콘텐츠 추출: {self.input_path.name}")

        # 1. 슬롯 파싱
        slots = self._parse_slots()
        print(f"  슬롯: {len(slots)}개")

        # 2. 템플릿 ID 생성
        template_id = self._generate_template_id()
        print(f"  템플릿 ID: {template_id}")

        # 3. 템플릿 객체 생성
        template = ImageContentTemplate(
            id=template_id,
            category=self.category,
            pattern=self.slots_data.get('pattern', 'custom'),
            slots=slots,
            semantic_description=self.slots_data.get('semantic_description', ''),
            match_keywords=self.slots_data.get('keywords', [self.category]),
            source_file=self.input_path.name
        )

        # 4. 저장
        self._save_template(template)

        # 5. 레지스트리 업데이트
        self._update_registry(template)

        print(f"\n  완료: {template.output_path}")
        return [template]

    def _parse_slots(self) -> List[SlotInfo]:
        """slots_data에서 SlotInfo 목록 생성."""
        slots = []
        for slot_data in self.slots_data.get('slots', []):
            slot = SlotInfo(
                name=slot_data.get('name', 'unnamed'),
                type=slot_data.get('type', 'text'),
                required=slot_data.get('required', True),
                position=slot_data.get('position', {}),
                example=slot_data.get('example'),
                item_schema=slot_data.get('item_schema'),
                count=slot_data.get('count')
            )
            slots.append(slot)
        return slots

    def _generate_template_id(self) -> str:
        """템플릿 ID 생성."""
        if self.template_name:
            return self.template_name

        # 파일명 기반 + 타임스탬프
        base_name = self.input_path.stem
        # 파일명에서 특수문자 제거
        base_name = ''.join(c if c.isalnum() or c == '-' else '-' for c in base_name)
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"{self.category}-{base_name}-{timestamp}"

    def _save_template(self, template: ImageContentTemplate) -> None:
        """템플릿 저장 (YAML + HTML + 썸네일)."""
        # 출력 경로 결정
        if self.output_path:
            output_dir = self.output_path
        else:
            base_dir = Path(__file__).parent.parent.parent.parent.parent
            output_dir = base_dir / 'templates' / 'contents' / template.category / template.id

        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"  저장 경로: {output_dir}")

        # 1. template.yaml
        self._save_yaml(template, output_dir)

        # 2. template.html
        self._save_html(template, output_dir)

        # 3. thumbnail.png (원본 이미지 복사/변환)
        self._save_thumbnail(output_dir)

        template.output_path = output_dir

    def _save_yaml(self, template: ImageContentTemplate, output_dir: Path) -> None:
        """template.yaml 저장."""
        yaml_data = {
            'id': template.id,
            'category': template.category,
            'pattern': template.pattern,
            'source_type': 'image',
            'has_ooxml': False,
            'render_method': 'html',
            'slots': [
                {
                    'name': s.name,
                    'type': s.type,
                    'required': s.required,
                    **(
                        {'position': s.position} if s.position else {}
                    ),
                    **(
                        {'example': s.example} if s.example else {}
                    ),
                    **(
                        {'item_schema': s.item_schema} if s.item_schema else {}
                    ),
                    **(
                        {'count': s.count} if s.count else {}
                    )
                }
                for s in template.slots
            ],
            'semantic_description': template.semantic_description,
            'match_keywords': template.match_keywords,
            'source_file': template.source_file,
            'extracted_at': datetime.now().strftime('%Y-%m-%d')
        }

        yaml_path = output_dir / 'template.yaml'
        header = f"콘텐츠 템플릿 (이미지 추출): {template.id}\n카테고리: {template.category}"
        save_yaml(yaml_data, yaml_path, header=header)
        print(f"    YAML: {yaml_path.name}")

    def _save_html(self, template: ImageContentTemplate, output_dir: Path) -> None:
        """template.html 저장 (Handlebars 템플릿)."""
        # slots_data에 html_template이 있으면 사용
        if 'html_template' in self.slots_data:
            html_content = self.slots_data['html_template']
        else:
            # 기본 HTML 생성
            html_content = self._generate_default_html(template)

        html_path = output_dir / 'template.html'
        html_path.write_text(html_content, encoding='utf-8')
        print(f"    HTML: {html_path.name}")

    def _generate_default_html(self, template: ImageContentTemplate) -> str:
        """기본 HTML 템플릿 생성."""
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '  <meta charset="UTF-8">',
            '  <style>',
            '    :root {',
            '      --primary: {{theme.primary}};',
            '      --background: {{theme.background}};',
            '      --text: {{theme.text}};',
            '    }',
            '    .slide {',
            '      width: 1920px;',
            '      height: 1080px;',
            '      background: var(--background);',
            '      color: var(--text);',
            '      position: relative;',
            '      font-family: sans-serif;',
            '    }',
            '    .element { position: absolute; }',
            '  </style>',
            '</head>',
            '<body>',
            '  <div class="slide">',
        ]

        for slot in template.slots:
            pos = slot.position
            style_parts = []
            if pos:
                style_parts.append(f"left: {pos.get('x', 0)}%")
                style_parts.append(f"top: {pos.get('y', 0)}%")
                style_parts.append(f"width: {pos.get('width', 100)}%")
                if pos.get('height'):
                    style_parts.append(f"height: {pos.get('height')}%")
            style = '; '.join(style_parts)
            style_attr = f' style="{style}"' if style else ''

            if slot.type == 'text':
                html_parts.append(
                    f'    <div class="element {slot.name}"{style_attr}>'
                    f'{{{{{slot.name}}}}}</div>'
                )
            elif slot.type == 'image':
                html_parts.append(
                    f'    <img class="element {slot.name}"{style_attr} '
                    f'src="{{{{{slot.name}}}}}" />'
                )
            elif slot.type == 'array':
                html_parts.append(f'    {{{{#each {slot.name}}}}}')
                html_parts.append(f'    <div class="element item">{{{{this}}}}</div>')
                html_parts.append('    {{/each}}')

        html_parts.extend([
            '  </div>',
            '</body>',
            '</html>'
        ])

        return '\n'.join(html_parts)

    def _save_thumbnail(self, output_dir: Path) -> None:
        """썸네일 저장 (원본 이미지 복사/변환)."""
        thumbnail_path = output_dir / 'thumbnail.png'

        # 원본 이미지가 PNG가 아니면 변환 필요
        if self.input_path.suffix.lower() == '.png':
            shutil.copy2(self.input_path, thumbnail_path)
        else:
            try:
                from PIL import Image
                img = Image.open(self.input_path)
                # 썸네일 크기로 리사이즈 (320x180)
                img.thumbnail((320, 180), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 'PNG')
            except ImportError:
                # PIL 없으면 그냥 복사
                shutil.copy2(self.input_path, thumbnail_path)

        print(f"    썸네일: {thumbnail_path.name}")

    def _update_registry(self, template: ImageContentTemplate) -> None:
        """레지스트리 업데이트."""
        try:
            from scripts.registry_manager import RegistryManager
            manager = RegistryManager()
            # 해당 카테고리의 레지스트리만 재빌드
            if template.output_path:
                manager.update_content(template.output_path)
            print("  레지스트리 업데이트 완료")
        except Exception as e:
            print(f"  Warning: 레지스트리 업데이트 실패: {e}")


if __name__ == '__main__':
    # 테스트용
    import argparse

    parser = argparse.ArgumentParser(description='이미지에서 콘텐츠 템플릿 추출')
    parser.add_argument('input', help='입력 이미지 경로')
    parser.add_argument('--slots-json', required=True, help='슬롯 정의 JSON')
    parser.add_argument('--category', '-c', help='카테고리')
    parser.add_argument('--name', '-n', help='템플릿 이름')
    parser.add_argument('--output', '-o', help='출력 경로')

    args = parser.parse_args()

    try:
        slots_data = json.loads(args.slots_json)
    except json.JSONDecodeError as e:
        print(f"Error: JSON 파싱 실패: {e}")
        sys.exit(1)

    extractor = ImageContentExtractor(
        input_path=Path(args.input),
        slots_data=slots_data,
        category=args.category,
        output_path=Path(args.output) if args.output else None,
        template_name=args.name
    )

    templates = extractor.run()
    print(f"\n추출 완료: {len(templates)}개 템플릿")
