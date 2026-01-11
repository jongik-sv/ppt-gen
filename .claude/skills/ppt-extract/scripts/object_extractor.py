#!/usr/bin/env python3
"""
Object Extractor.

감지된 오브젝트를 PNG + metadata.yaml + thumbnail.png로 저장합니다.

출력 구조:
    templates/objects/{category}/{object_id}/
    ├── object.png          # 원본 이미지 (PowerPoint 렌더링)
    ├── metadata.yaml       # 메타데이터 + text_overlays
    └── thumbnail.png       # 미리보기 (320x180)
"""

import re
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 스크립트 디렉토리를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared.yaml_utils import save_yaml
from scripts.thumbnail import (
    convert_pptx_to_images,
    create_thumbnail,
    THUMBNAIL_SIZES,
    HAS_PIL
)
from scripts.object_detector import ObjectCandidate, ObjectCategory, ShapeInfo

if HAS_PIL:
    from PIL import Image


# 오브젝트 썸네일 크기
OBJECT_THUMBNAIL_SIZE = (320, 180)


@dataclass
class TextOverlay:
    """텍스트 오버레이 정보."""
    id: str
    position: Dict[str, str]  # x%, y%
    text: str
    font_size: Optional[float] = None
    alignment: str = "center"


@dataclass
class ObjectMetadata:
    """오브젝트 메타데이터."""
    id: str
    category: str
    name: str
    description: str
    text_overlays: List[TextOverlay]
    keywords: List[str]
    detection_type: str
    confidence: float
    source_file: Optional[str] = None
    slide_index: int = 0
    extracted_at: str = ""


class ObjectExtractor:
    """오브젝트 추출기."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Args:
            templates_dir: 템플릿 루트 디렉토리 (기본: ppt-gen/templates)
        """
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # 기본 경로: ppt-gen/templates
            self.templates_dir = SCRIPT_DIR.parent.parent.parent / 'templates'

        self.objects_dir = self.templates_dir / 'objects'

    def extract(
        self,
        pptx_path: Path,
        slide_index: int,
        candidate: ObjectCandidate,
        object_id: Optional[str] = None
    ) -> Optional[Path]:
        """
        오브젝트 후보를 추출하여 저장합니다.

        Args:
            pptx_path: 원본 PPTX 파일 경로
            slide_index: 슬라이드 인덱스 (0-based)
            candidate: 감지된 오브젝트 후보
            object_id: 오브젝트 ID (지정하지 않으면 자동 생성)

        Returns:
            저장된 오브젝트 디렉토리 경로, 실패 시 None
        """
        pptx_path = Path(pptx_path)

        # 오브젝트 ID 생성
        if not object_id:
            object_id = self._generate_object_id(candidate, pptx_path.stem)

        # 출력 디렉토리
        category = candidate.category.value
        output_dir = self.objects_dir / category / object_id
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n오브젝트 추출: {object_id}")
        print(f"  카테고리: {category}")
        print(f"  감지 유형: {candidate.detection_type.value}")
        print(f"  신뢰도: {candidate.confidence:.2f}")

        try:
            # 1. 오브젝트 이미지 캡처
            object_png = self._capture_object_image(
                pptx_path, slide_index, candidate.bounding_box, output_dir
            )
            if object_png:
                print(f"  이미지: {object_png.name}")

            # 2. 텍스트 오버레이 추출
            text_overlays = self._extract_text_overlays(
                candidate.shapes, candidate.bounding_box
            )
            print(f"  텍스트 오버레이: {len(text_overlays)}개")

            # 3. 메타데이터 생성
            metadata = self._generate_metadata(
                object_id, candidate, text_overlays, pptx_path.name, slide_index
            )
            self._save_metadata(metadata, output_dir)
            print(f"  메타데이터: metadata.yaml")

            # 4. 썸네일 생성
            if object_png and object_png.exists():
                thumbnail_path = output_dir / 'thumbnail.png'
                self._generate_thumbnail(object_png, thumbnail_path)
                print(f"  썸네일: thumbnail.png")

            return output_dir

        except Exception as e:
            print(f"  오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_object_id(self, candidate: ObjectCandidate, source_name: str) -> str:
        """오브젝트 ID 생성."""
        # 카테고리 + 감지 유형 + 타임스탬프
        category = candidate.category.value
        detection = candidate.detection_type.value.replace('_', '-')
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')

        # 소스 이름에서 안전한 문자만 추출
        safe_source = re.sub(r'[^\w\-]', '', source_name.replace(' ', '-'))[:20]

        return f"{safe_source}-{detection}-{timestamp}"

    def _capture_object_image(
        self,
        pptx_path: Path,
        slide_index: int,
        bounding_box: Tuple[float, float, float, float],
        output_dir: Path
    ) -> Optional[Path]:
        """
        오브젝트 영역을 이미지로 캡처합니다.

        전체 슬라이드를 렌더링한 후 바운딩 박스 영역만 크롭합니다.
        """
        if not HAS_PIL:
            print("  경고: PIL이 없어 이미지 캡처를 건너뜁니다")
            return None

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # PPTX → 이미지 변환
                images = convert_pptx_to_images(pptx_path, temp_path)

                if slide_index >= len(images):
                    print(f"  경고: 슬라이드 {slide_index}가 존재하지 않습니다")
                    return None

                slide_image_path = images[slide_index]

                # 이미지 열기 및 크롭
                with Image.open(slide_image_path) as img:
                    img_width, img_height = img.size

                    # 바운딩 박스 (%)를 픽셀로 변환
                    x, y, w, h = bounding_box
                    left = int(x / 100 * img_width)
                    top = int(y / 100 * img_height)
                    right = int((x + w) / 100 * img_width)
                    bottom = int((y + h) / 100 * img_height)

                    # 여백 추가 (5%)
                    margin_x = int(w / 100 * img_width * 0.05)
                    margin_y = int(h / 100 * img_height * 0.05)
                    left = max(0, left - margin_x)
                    top = max(0, top - margin_y)
                    right = min(img_width, right + margin_x)
                    bottom = min(img_height, bottom + margin_y)

                    # 크롭
                    cropped = img.crop((left, top, right, bottom))

                    # 저장
                    output_path = output_dir / 'object.png'
                    cropped.save(output_path, 'PNG')

                    return output_path

        except FileNotFoundError as e:
            print(f"  경고: 이미지 변환 도구 미설치: {e}")
            return None
        except Exception as e:
            print(f"  경고: 이미지 캡처 실패: {e}")
            return None

    def _extract_text_overlays(
        self,
        shapes: List[ShapeInfo],
        bounding_box: Tuple[float, float, float, float]
    ) -> List[TextOverlay]:
        """
        도형에서 텍스트 오버레이 정보를 추출합니다.

        텍스트가 있는 도형의 위치를 오브젝트 바운딩 박스 기준 상대 좌표로 변환합니다.
        """
        overlays = []
        obj_x, obj_y, obj_w, obj_h = bounding_box

        # 텍스트가 있는 도형 필터링
        text_shapes = [s for s in shapes if s.text and not s.is_connector]

        for i, shape in enumerate(text_shapes):
            # 도형 중심점 계산
            shape_x = shape.position.get('x', 0)
            shape_y = shape.position.get('y', 0)
            shape_w = shape.position.get('width', 0)
            shape_h = shape.position.get('height', 0)

            center_x = shape_x + shape_w / 2
            center_y = shape_y + shape_h / 2

            # 오브젝트 기준 상대 좌표 (%)
            if obj_w > 0 and obj_h > 0:
                rel_x = (center_x - obj_x) / obj_w * 100
                rel_y = (center_y - obj_y) / obj_h * 100
            else:
                rel_x = 50
                rel_y = 50

            # 텍스트 ID 생성
            overlay_id = self._generate_overlay_id(shape, i)

            overlay = TextOverlay(
                id=overlay_id,
                position={
                    'x': f"{rel_x:.1f}%",
                    'y': f"{rel_y:.1f}%"
                },
                text=shape.text.strip()[:100],  # 최대 100자
                font_size=shape.style.get('font_size'),
                alignment=self._infer_alignment(shape)
            )
            overlays.append(overlay)

        return overlays

    def _generate_overlay_id(self, shape: ShapeInfo, index: int) -> str:
        """텍스트 오버레이 ID 생성."""
        # 이름이 있으면 사용
        if shape.name:
            safe_name = re.sub(r'[^\w\-]', '', shape.name.replace(' ', '_'))[:20]
            if safe_name:
                return safe_name.lower()

        # 없으면 인덱스 사용
        return f"text_{index + 1}"

    def _infer_alignment(self, shape: ShapeInfo) -> str:
        """도형 위치에서 정렬 추론."""
        x = shape.position.get('x', 50)

        # 좌측 30% 이내
        if x < 30:
            return "left"
        # 우측 70% 이후
        elif x > 70:
            return "right"
        else:
            return "center"

    def _generate_metadata(
        self,
        object_id: str,
        candidate: ObjectCandidate,
        text_overlays: List[TextOverlay],
        source_file: str,
        slide_index: int
    ) -> ObjectMetadata:
        """메타데이터 생성."""
        # 이름 생성
        name = self._generate_name(candidate)

        # 설명 생성
        description = self._generate_description(candidate)

        # 키워드 추출
        keywords = self._extract_keywords(candidate, text_overlays)

        return ObjectMetadata(
            id=object_id,
            category=candidate.category.value,
            name=name,
            description=description,
            text_overlays=text_overlays,
            keywords=keywords,
            detection_type=candidate.detection_type.value,
            confidence=candidate.confidence,
            source_file=source_file,
            slide_index=slide_index + 1,  # 1-based
            extracted_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def _generate_name(self, candidate: ObjectCandidate) -> str:
        """오브젝트 이름 생성."""
        category_names = {
            ObjectCategory.DIAGRAM: "다이어그램",
            ObjectCategory.PROCESS: "프로세스",
            ObjectCategory.CHART: "차트"
        }

        detection_names = {
            'group_5plus': "복합 도형",
            'nonlinear': "비선형 배치",
            'connector': "플로우차트",
            'chart': "데이터 차트",
            'matrix': "매트릭스"
        }

        category_name = category_names.get(candidate.category, "오브젝트")
        detection_name = detection_names.get(candidate.detection_type.value, "")

        if detection_name:
            return f"{detection_name} {category_name}"
        return category_name

    def _generate_description(self, candidate: ObjectCandidate) -> str:
        """오브젝트 설명 생성."""
        parts = [candidate.reason]

        shape_count = len([s for s in candidate.shapes if not getattr(s, 'is_connector', False)])
        if shape_count > 0:
            parts.append(f"도형 {shape_count}개 포함")

        text_count = len([s for s in candidate.shapes if s.text])
        if text_count > 0:
            parts.append(f"텍스트 {text_count}개")

        return ". ".join(parts)

    def _extract_keywords(
        self,
        candidate: ObjectCandidate,
        text_overlays: List[TextOverlay]
    ) -> List[str]:
        """키워드 추출."""
        keywords = set()

        # 카테고리 기반
        category_keywords = {
            ObjectCategory.DIAGRAM: ['다이어그램', 'diagram', '순환', '사이클'],
            ObjectCategory.PROCESS: ['프로세스', 'process', '플로우', '단계'],
            ObjectCategory.CHART: ['차트', 'chart', '그래프', '데이터']
        }
        keywords.update(category_keywords.get(candidate.category, [])[:2])

        # 감지 유형 기반
        detection_keywords = {
            'group_5plus': ['복합', '그룹'],
            'nonlinear': ['원형', '방사형'],
            'connector': ['연결', '화살표'],
            'chart': ['시각화', '통계'],
            'matrix': ['매트릭스', '벤다이어그램']
        }
        keywords.update(detection_keywords.get(candidate.detection_type.value, []))

        # 텍스트에서 추출
        for overlay in text_overlays[:5]:  # 최대 5개
            words = overlay.text.split()
            for word in words[:2]:  # 각 텍스트에서 2단어
                if len(word) >= 2:
                    keywords.add(word)

        return list(keywords)[:10]  # 최대 10개

    def _save_metadata(self, metadata: ObjectMetadata, output_dir: Path) -> None:
        """metadata.yaml 저장."""
        yaml_data = {
            'id': metadata.id,
            'category': metadata.category,
            'name': metadata.name,
            'description': metadata.description,
            'text_overlays': [
                {
                    'id': o.id,
                    'position': o.position,
                    'text': o.text,
                    **(
                        {'font_size': o.font_size} if o.font_size else {}
                    ),
                    **(
                        {'alignment': o.alignment} if o.alignment != 'center' else {}
                    )
                }
                for o in metadata.text_overlays
            ],
            'keywords': metadata.keywords,
            'detection_type': metadata.detection_type,
            'confidence': round(metadata.confidence, 2),
            'source_file': metadata.source_file,
            'slide_index': metadata.slide_index,
            'extracted_at': metadata.extracted_at
        }

        yaml_path = output_dir / 'metadata.yaml'
        header = f"오브젝트: {metadata.name}\n카테고리: {metadata.category}"
        save_yaml(yaml_data, yaml_path, header=header)

    def _generate_thumbnail(self, source_path: Path, output_path: Path) -> None:
        """썸네일 생성."""
        if not HAS_PIL:
            return

        try:
            create_thumbnail(source_path, OBJECT_THUMBNAIL_SIZE, output_path)
        except Exception as e:
            print(f"  경고: 썸네일 생성 실패: {e}")


def main():
    """CLI 엔트리포인트 (테스트용)."""
    import argparse

    parser = argparse.ArgumentParser(description="오브젝트 추출 테스트")
    parser.add_argument("input", help="입력 PPTX 파일")
    parser.add_argument("--slide", type=int, default=0, help="슬라이드 인덱스 (0-based)")
    parser.add_argument("--output-dir", help="출력 디렉토리")

    args = parser.parse_args()

    # 테스트: 전체 슬라이드를 오브젝트로 추출
    from scripts.object_detector import ObjectDetector, DetectionType

    pptx_path = Path(args.input)

    # 간단한 테스트용 후보 생성
    test_candidate = ObjectCandidate(
        shapes=[],
        detection_type=DetectionType.GROUP_5PLUS,
        confidence=0.8,
        bounding_box=(10, 10, 80, 80),
        category=ObjectCategory.DIAGRAM,
        reason="테스트 추출"
    )

    extractor = ObjectExtractor()
    if args.output_dir:
        extractor.objects_dir = Path(args.output_dir)

    result = extractor.extract(pptx_path, args.slide, test_candidate)
    if result:
        print(f"\n추출 완료: {result}")
    else:
        print("\n추출 실패")


if __name__ == "__main__":
    main()
