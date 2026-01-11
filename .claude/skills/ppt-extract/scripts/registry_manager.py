"""
Registry Manager - 템플릿 레지스트리 자동 관리.

templates/ 폴더의 모든 template.yaml을 스캔하여
카테고리별 registry.yaml을 자동 생성/업데이트합니다.

Usage:
    from scripts.registry_manager import RegistryManager

    manager = RegistryManager()
    manager.rebuild_all()  # 전체 재빌드
    manager.update_document(doc_path)  # 개별 업데이트
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class RegistryManager:
    """템플릿 레지스트리 관리자."""

    def __init__(self, templates_root: Optional[Path] = None):
        """초기화.

        Args:
            templates_root: templates 폴더 경로 (기본: 프로젝트 루트/templates)
        """
        if templates_root:
            self.templates_root = Path(templates_root)
        else:
            # 스크립트 위치 기준으로 templates 폴더 찾기
            script_dir = Path(__file__).parent
            self.templates_root = script_dir.parent.parent.parent.parent / 'templates'

        self.documents_dir = self.templates_root / 'documents'
        self.contents_dir = self.templates_root / 'contents'
        self.themes_dir = self.templates_root / 'themes'
        self.objects_dir = self.templates_root / 'objects'

    def rebuild_all(self) -> Dict[str, int]:
        """모든 레지스트리 재빌드.

        Returns:
            카테고리별 등록 항목 수
        """
        results = {}

        # 문서 양식 레지스트리
        if self.documents_dir.exists():
            count = self._rebuild_documents_registry()
            results['documents'] = count

        # 콘텐츠 레지스트리 (카테고리별)
        if self.contents_dir.exists():
            for category_dir in self.contents_dir.iterdir():
                if category_dir.is_dir():
                    count = self._rebuild_content_category_registry(category_dir)
                    results[f'contents/{category_dir.name}'] = count

        # 테마 레지스트리
        if self.themes_dir.exists():
            count = self._rebuild_themes_registry()
            results['themes'] = count

        # 오브젝트 레지스트리 (카테고리별)
        if self.objects_dir.exists():
            for category_dir in self.objects_dir.iterdir():
                if category_dir.is_dir():
                    count = self._rebuild_objects_category_registry(category_dir)
                    results[f'objects/{category_dir.name}'] = count

        return results

    def _rebuild_documents_registry(self) -> int:
        """문서 양식 레지스트리 재빌드."""
        entries = []

        for group_dir in self.documents_dir.iterdir():
            if not group_dir.is_dir():
                continue

            for template_dir in group_dir.iterdir():
                if not template_dir.is_dir():
                    continue

                template_yaml = template_dir / 'template.yaml'
                if not template_yaml.exists():
                    continue

                try:
                    with open(template_yaml, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)

                    doc = data.get('document', {})
                    entry = {
                        'id': doc.get('id', template_dir.name),
                        'name': doc.get('name', template_dir.name),
                        'group': doc.get('group', group_dir.name),
                        'source_file': doc.get('source_file', ''),
                        'path': str(template_dir.relative_to(self.templates_root)),
                        'extracted_at': doc.get('extracted_at', ''),
                        'layouts_count': len(data.get('layouts', [])),
                    }
                    entries.append(entry)
                except Exception as e:
                    print(f"Warning: {template_yaml} 읽기 실패: {e}")

        # 레지스트리 저장
        registry = {
            'type': 'documents',
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'count': len(entries),
            'entries': sorted(entries, key=lambda x: x['id'])
        }

        registry_path = self.documents_dir / 'registry.yaml'
        with open(registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(registry, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return len(entries)

    def _rebuild_content_category_registry(self, category_dir: Path) -> int:
        """콘텐츠 카테고리 레지스트리 재빌드."""
        entries = []

        for template_dir in category_dir.iterdir():
            if not template_dir.is_dir():
                continue

            template_yaml = template_dir / 'template.yaml'
            if not template_yaml.exists():
                continue

            try:
                with open(template_yaml, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                content = data.get('content', data)  # content 키 또는 루트
                entry = {
                    'id': content.get('id', template_dir.name),
                    'name': content.get('name', template_dir.name),
                    'source_document': content.get('source_document', content.get('document_style', '')),
                    'source_type': content.get('source_type', 'pptx'),  # pptx 또는 image
                    'has_ooxml': content.get('has_ooxml', True),
                    'path': str(template_dir.relative_to(self.templates_root)),
                    'extracted_at': content.get('extracted_at', ''),
                    'render_method': content.get('render_method', 'ooxml' if content.get('has_ooxml', True) else 'html'),
                }

                # vmin 메타데이터 (있으면 포함)
                if content.get('vmin'):
                    entry['vmin'] = content.get('vmin')
                if content.get('slide_size'):
                    entry['slide_size'] = content.get('slide_size')

                # 썸네일 경로 추가
                thumbnail = template_dir / 'thumbnail.png'
                if thumbnail.exists():
                    entry['thumbnail'] = str(thumbnail.relative_to(self.templates_root))

                entries.append(entry)
            except Exception as e:
                print(f"Warning: {template_yaml} 읽기 실패: {e}")

        # 레지스트리 저장
        registry = {
            'type': 'contents',
            'category': category_dir.name,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'count': len(entries),
            'entries': sorted(entries, key=lambda x: x['id'])
        }

        registry_path = category_dir / 'registry.yaml'
        with open(registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(registry, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return len(entries)

    def _rebuild_themes_registry(self) -> int:
        """테마 레지스트리 재빌드."""
        entries = []

        for theme_dir in self.themes_dir.iterdir():
            if not theme_dir.is_dir():
                continue

            theme_yaml = theme_dir / 'theme.yaml'
            if not theme_yaml.exists():
                continue

            try:
                with open(theme_yaml, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                entry = {
                    'id': data.get('id', theme_dir.name),
                    'name': data.get('name', theme_dir.name),
                    'source': data.get('source', ''),
                    'path': str(theme_dir.relative_to(self.templates_root)),
                    'extracted_at': data.get('extracted_at', ''),
                }

                # 주요 색상 포함
                colors = data.get('colors', {})
                if colors:
                    entry['primary_color'] = colors.get('accent1', colors.get('primary', ''))

                entries.append(entry)
            except Exception as e:
                print(f"Warning: {theme_yaml} 읽기 실패: {e}")

        # 레지스트리 저장
        registry = {
            'type': 'themes',
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'count': len(entries),
            'entries': sorted(entries, key=lambda x: x['id'])
        }

        registry_path = self.themes_dir / 'registry.yaml'
        with open(registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(registry, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return len(entries)

    def _rebuild_objects_category_registry(self, category_dir: Path) -> int:
        """오브젝트 카테고리 레지스트리 재빌드."""
        entries = []

        for object_dir in category_dir.iterdir():
            if not object_dir.is_dir():
                continue

            metadata_yaml = object_dir / 'metadata.yaml'
            if not metadata_yaml.exists():
                continue

            try:
                with open(metadata_yaml, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                entry = {
                    'id': data.get('id', object_dir.name),
                    'name': data.get('name', object_dir.name),
                    'category': data.get('category', category_dir.name),
                    'path': str(object_dir.relative_to(self.templates_root)),
                    'detection_type': data.get('detection_type', ''),
                    'confidence': data.get('confidence', 0),
                    'extracted_at': data.get('extracted_at', ''),
                }

                # 키워드 포함
                keywords = data.get('keywords', [])
                if keywords:
                    entry['keywords'] = keywords[:5]  # 최대 5개

                # 썸네일 경로 추가
                thumbnail = object_dir / 'thumbnail.png'
                if thumbnail.exists():
                    entry['thumbnail'] = str(thumbnail.relative_to(self.templates_root))

                entries.append(entry)
            except Exception as e:
                print(f"Warning: {metadata_yaml} 읽기 실패: {e}")

        # 레지스트리 저장
        registry = {
            'type': 'objects',
            'category': category_dir.name,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'count': len(entries),
            'entries': sorted(entries, key=lambda x: x['id'])
        }

        registry_path = category_dir / 'registry.yaml'
        with open(registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(registry, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return len(entries)

    def update_document(self, doc_path: Path) -> bool:
        """단일 문서 레지스트리 업데이트.

        Args:
            doc_path: 문서 템플릿 경로

        Returns:
            성공 여부
        """
        # 문서 레지스트리 전체 재빌드 (간단한 구현)
        self._rebuild_documents_registry()
        return True

    def update_content(self, content_path: Path) -> bool:
        """단일 콘텐츠 레지스트리 업데이트.

        Args:
            content_path: 콘텐츠 템플릿 경로

        Returns:
            성공 여부
        """
        # 해당 카테고리만 재빌드
        category_dir = content_path.parent
        if category_dir.exists():
            self._rebuild_content_category_registry(category_dir)
        return True

    def update_theme(self, theme_path: Path) -> bool:
        """단일 테마 레지스트리 업데이트.

        Args:
            theme_path: 테마 경로

        Returns:
            성공 여부
        """
        self._rebuild_themes_registry()
        return True

    def update_object(self, object_path: Path) -> bool:
        """단일 오브젝트 레지스트리 업데이트.

        Args:
            object_path: 오브젝트 경로

        Returns:
            성공 여부
        """
        # 해당 카테고리만 재빌드
        category_dir = object_path.parent
        if category_dir.exists():
            self._rebuild_objects_category_registry(category_dir)
        return True

    def find_objects_by_category(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 오브젝트 찾기.

        Args:
            category: 카테고리 (diagram, process, chart)

        Returns:
            오브젝트 목록
        """
        category_dir = self.objects_dir / category
        registry_path = category_dir / 'registry.yaml'

        if not registry_path.exists():
            if category_dir.exists():
                self._rebuild_objects_category_registry(category_dir)
            else:
                return []

        if not registry_path.exists():
            return []

        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f)

        return registry.get('entries', [])

    def find_objects_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """키워드로 오브젝트 검색.

        Args:
            keyword: 검색 키워드

        Returns:
            매칭된 오브젝트 목록
        """
        results = []
        keyword_lower = keyword.lower()

        if not self.objects_dir.exists():
            return results

        for category_dir in self.objects_dir.iterdir():
            if not category_dir.is_dir():
                continue

            registry_path = category_dir / 'registry.yaml'
            if not registry_path.exists():
                continue

            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = yaml.safe_load(f)

            for entry in registry.get('entries', []):
                # 이름, 키워드에서 검색
                name_match = keyword_lower in entry.get('name', '').lower()
                keywords = entry.get('keywords', [])
                keyword_match = any(keyword_lower in kw.lower() for kw in keywords)

                if name_match or keyword_match:
                    results.append(entry)

        return results

    def find_document_by_source(self, source_file: str) -> Optional[Dict[str, Any]]:
        """source_file로 문서 찾기.

        Args:
            source_file: 원본 파일명

        Returns:
            문서 정보 또는 None
        """
        registry_path = self.documents_dir / 'registry.yaml'
        if not registry_path.exists():
            self._rebuild_documents_registry()

        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f)

        for entry in registry.get('entries', []):
            if entry.get('source_file') == source_file:
                return entry

        return None

    def find_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """ID로 문서 찾기.

        Args:
            doc_id: 문서 ID

        Returns:
            문서 정보 또는 None
        """
        registry_path = self.documents_dir / 'registry.yaml'
        if not registry_path.exists():
            self._rebuild_documents_registry()

        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f)

        for entry in registry.get('entries', []):
            if entry.get('id') == doc_id:
                return entry

        return None

    def find_contents_by_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """문서 ID로 연관 콘텐츠 찾기.

        Args:
            doc_id: 문서 ID

        Returns:
            연관 콘텐츠 목록
        """
        related = []

        if not self.contents_dir.exists():
            return related

        for category_dir in self.contents_dir.iterdir():
            if not category_dir.is_dir():
                continue

            registry_path = category_dir / 'registry.yaml'
            if not registry_path.exists():
                continue

            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = yaml.safe_load(f)

            for entry in registry.get('entries', []):
                # source_document 일치 또는 ID 접두사 매칭
                if entry.get('source_document') == doc_id:
                    related.append(entry)
                elif entry.get('id', '').startswith(doc_id.split('-')[0] + '-'):
                    related.append(entry)

        return related

    def delete_document(self, doc_id: str, cascade: bool = False, dry_run: bool = False) -> Dict[str, List[str]]:
        """문서 삭제.

        Args:
            doc_id: 문서 ID
            cascade: 연관 콘텐츠도 삭제
            dry_run: 삭제하지 않고 대상만 반환

        Returns:
            삭제 대상 경로 목록
        """
        import shutil

        targets = {
            'documents': [],
            'contents': [],
            'thumbnails': []
        }

        # 문서 찾기
        doc = self.find_document_by_id(doc_id)
        if doc:
            doc_path = self.templates_root / doc['path']
            targets['documents'].append(str(doc_path))

        # 연관 콘텐츠 찾기
        if cascade:
            related = self.find_contents_by_document(doc_id)
            for content in related:
                content_path = self.templates_root / content['path']
                targets['contents'].append(str(content_path))

                # 썸네일
                if 'thumbnail' in content:
                    thumb_path = self.templates_root / content['thumbnail']
                    targets['thumbnails'].append(str(thumb_path))

        if dry_run:
            return targets

        # 실제 삭제
        for path_list in targets.values():
            for path_str in path_list:
                path = Path(path_str)
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()

        # 레지스트리 재빌드
        self.rebuild_all()

        return targets


def rebuild_registry():
    """CLI용 레지스트리 재빌드 함수."""
    manager = RegistryManager()
    results = manager.rebuild_all()

    print("\n=== 레지스트리 재빌드 완료 ===")
    for category, count in results.items():
        print(f"  {category}: {count}개")

    return results


if __name__ == '__main__':
    rebuild_registry()
