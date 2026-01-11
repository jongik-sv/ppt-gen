#!/usr/bin/env python3
"""
Style Extractor.

PPTX 또는 이미지에서 테마(색상, 폰트)를 추출합니다.
"""

import re
import sys
from pathlib import Path
from typing import Dict, Optional

# 스크립트 디렉토리를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared.ooxml_parser import OOXMLParser
from shared.yaml_utils import save_yaml
from shared.color_utils import (
    map_ooxml_colors_to_theme,
    extract_colors_from_image,
    classify_colors_by_role,
    generate_palette_thumbnail
)


def normalize_theme_name(name: str) -> str:
    """테마 이름을 케밥케이스로 정규화."""
    # 공백, 언더스코어를 하이픈으로
    name = re.sub(r'[\s_]+', '-', name)
    # 연속 하이픈 제거
    name = re.sub(r'-+', '-', name)
    # 앞뒤 하이픈 제거
    name = name.strip('-')
    # 소문자로
    name = name.lower()
    return name


class StyleExtractor:
    """테마 추출기."""

    def __init__(
        self,
        input_path: Path,
        name: str,
        output_path: Optional[Path] = None
    ):
        """
        Args:
            input_path: 입력 파일 경로 (PPTX 또는 이미지)
            name: 테마 이름
            output_path: 출력 경로 (기본: templates/themes/{name}/)
        """
        self.input_path = Path(input_path)
        self.name = normalize_theme_name(name)

        if output_path:
            self.output_path = Path(output_path)
        else:
            # 기본 경로: templates/themes/{name}/
            self.output_path = SCRIPT_DIR.parent.parent.parent / 'templates' / 'themes' / self.name

        self.is_pptx = self.input_path.suffix.lower() == '.pptx'

    def run(self) -> Dict:
        """
        테마 추출 실행.

        Returns:
            추출된 테마 데이터
        """
        print(f"\n테마 추출 시작: {self.input_path.name}")
        print(f"  출력 경로: {self.output_path}")

        if self.is_pptx:
            theme_data = self._extract_from_pptx()
        else:
            theme_data = self._extract_from_image()

        # 테마 저장
        self._save_theme(theme_data)

        # 레지스트리 업데이트
        print("\n레지스트리 업데이트 중...")
        try:
            from scripts.registry_manager import RegistryManager
            manager = RegistryManager()
            manager.update_theme(self.output_path)
        except Exception as e:
            print(f"  Warning: 레지스트리 업데이트 실패: {e}")

        return theme_data

    def _extract_from_pptx(self) -> Dict:
        """PPTX에서 테마 추출."""
        print("\n  PPTX 테마 분석 중...")

        parser = OOXMLParser(self.input_path)

        # 색상 추출
        ooxml_colors = parser.extract_theme_colors()
        print(f"    OOXML 색상: {len(ooxml_colors)}개")

        # 역할 매핑
        theme_colors = map_ooxml_colors_to_theme(ooxml_colors)
        print(f"    테마 색상: {len(theme_colors)}개")

        # 폰트 추출
        fonts = parser.extract_theme_fonts()
        print(f"    폰트: major={fonts.get('major', 'N/A')}, minor={fonts.get('minor', 'N/A')}")

        return {
            'id': self.name,
            'name': self.name.replace('-', ' ').title(),
            'source_type': 'pptx',
            'source_file': self.input_path.name,
            'colors': theme_colors,
            'fonts': {
                'major': fonts.get('major') or fonts.get('major_ea', 'Arial'),
                'minor': fonts.get('minor') or fonts.get('minor_ea', 'Arial')
            },
            'ooxml_colors': ooxml_colors  # 원본 OOXML 색상 보존
        }

    def _extract_from_image(self) -> Dict:
        """이미지에서 테마 추출."""
        print("\n  이미지 색상 분석 중...")

        # K-means 클러스터링으로 주요 색상 추출
        try:
            colors = extract_colors_from_image(self.input_path, n_colors=8)
            print(f"    추출된 색상: {len(colors)}개")
        except ImportError as e:
            print(f"    경고: {e}")
            print("    기본 색상을 사용합니다.")
            return self._get_default_theme()

        # 역할 분류
        theme_colors = classify_colors_by_role(colors)
        print(f"    역할 분류 완료")

        # 추출된 색상 목록 (참고용)
        extracted_hex = [c.hex for c in colors]

        return {
            'id': self.name,
            'name': self.name.replace('-', ' ').title(),
            'source_type': 'image',
            'source_file': self.input_path.name,
            'colors': theme_colors,
            'fonts': {
                'major': 'Pretendard',
                'minor': 'Pretendard'
            },
            'style_hints': {
                'border_radius': '16px',
                'shadow': '0 4px 12px rgba(0,0,0,0.08)'
            },
            'extracted_colors': extracted_hex  # 원본 추출 색상 보존
        }

    def _get_default_theme(self) -> Dict:
        """기본 테마 반환."""
        return {
            'id': self.name,
            'name': self.name.replace('-', ' ').title(),
            'source_type': 'default',
            'colors': {
                'primary': '#0066CC',
                'secondary': '#4A90D9',
                'accent': '#00A3E0',
                'background': '#FFFFFF',
                'surface': '#F5F5F5',
                'text': '#1A1A1A',
                'muted': '#6B7280'
            },
            'fonts': {
                'major': 'Pretendard',
                'minor': 'Pretendard'
            }
        }

    def _save_theme(self, theme_data: Dict) -> None:
        """테마 저장."""
        print("\n  테마 저장 중...")

        # 출력 디렉토리 생성
        self.output_path.mkdir(parents=True, exist_ok=True)

        # theme.yaml 저장
        yaml_path = self.output_path / 'theme.yaml'

        # YAML용 데이터 (일부 필드 제외)
        yaml_data = {
            'id': theme_data['id'],
            'name': theme_data['name'],
            'colors': theme_data['colors'],
            'fonts': theme_data['fonts']
        }

        # 스타일 힌트가 있으면 추가
        if 'style_hints' in theme_data:
            yaml_data['style_hints'] = theme_data['style_hints']

        header = f"테마: {theme_data['name']}\n원본: {theme_data.get('source_file', 'N/A')}"
        save_yaml(yaml_data, yaml_path, header=header)
        print(f"    저장됨: {yaml_path}")

        # 썸네일 생성
        thumbnail_path = self.output_path / 'thumbnail.png'
        try:
            generate_palette_thumbnail(theme_data['colors'], thumbnail_path)
            print(f"    썸네일: {thumbnail_path}")
        except Exception as e:
            print(f"    썸네일 생성 실패: {e}")

        print(f"\n완료: {self.output_path}")
