#!/usr/bin/env python3
"""
Slide Crawler - 온라인 슬라이드에서 콘텐츠 패턴 추출

SlideShare, Speaker Deck 등에서 슬라이드를 크롤링하여
콘텐츠 템플릿 YAML로 변환합니다.

Usage:
    python slide-crawler.py <url> --output <template_id>
    python slide-crawler.py "https://slideshare.net/..." --output timeline2 --category timeline

Examples:
    # SlideShare에서 크롤링
    python slide-crawler.py "https://www.slideshare.net/user/presentation" --output my-template

    # 카테고리 지정
    python slide-crawler.py "https://speakerdeck.com/user/deck" --output process1 --category process

    # 분석만 (저장 안함)
    python slide-crawler.py "https://slideshare.net/..." --analyze-only

Dependencies:
    pip install requests beautifulsoup4 Pillow
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin

import yaml

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# 공유 모듈 import
import sys
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent.parent / 'shared'))
from config import CONTENTS_DIR
from yaml_utils import load_registry, save_registry

# 레지스트리 경로
REGISTRY_PATH = CONTENTS_DIR / 'registry.yaml'


class SlideExtractor:
    """슬라이드 추출 베이스 클래스"""

    def __init__(self, url: str):
        self.url = url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def extract(self) -> dict:
        """슬라이드 정보 추출 → {'title', 'slides', 'metadata'}"""
        raise NotImplementedError

    def _get_page(self, url: str) -> BeautifulSoup:
        """페이지 가져오기"""
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')


class SlideShareExtractor(SlideExtractor):
    """SlideShare 슬라이드 추출"""

    def extract(self) -> dict:
        soup = self._get_page(self.url)

        result = {
            'title': '',
            'slides': [],
            'metadata': {
                'source': 'slideshare',
                'url': self.url,
            }
        }

        # 제목 추출
        title_elem = soup.select_one('h1.slideshow-title, h1[class*="title"]')
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)

        # 슬라이드 이미지 URL 추출
        # SlideShare는 이미지로 슬라이드를 제공
        slide_images = soup.select('img[class*="slide-image"], img[data-src*="slide"]')

        for i, img in enumerate(slide_images):
            src = img.get('data-src') or img.get('src', '')
            if src:
                result['slides'].append({
                    'index': i,
                    'image_url': src,
                    'type': 'image',
                })

        # 대체 방법: JSON 데이터에서 추출
        if not result['slides']:
            scripts = soup.find_all('script')
            for script in scripts:
                text = script.string or ''
                if 'slideImages' in text or 'slides' in text:
                    # JSON 패턴 매칭
                    urls = re.findall(r'https?://[^"\']+\.(?:jpg|png|jpeg)[^"\']*', text)
                    for i, url in enumerate(urls):
                        result['slides'].append({
                            'index': i,
                            'image_url': url,
                            'type': 'image',
                        })
                    break

        # 메타데이터
        author = soup.select_one('a[class*="author"], span[class*="author"]')
        if author:
            result['metadata']['author'] = author.get_text(strip=True)

        return result


class SpeakerDeckExtractor(SlideExtractor):
    """Speaker Deck 슬라이드 추출"""

    def extract(self) -> dict:
        soup = self._get_page(self.url)

        result = {
            'title': '',
            'slides': [],
            'metadata': {
                'source': 'speakerdeck',
                'url': self.url,
            }
        }

        # 제목 추출
        title_elem = soup.select_one('h1.deck-title, h1[class*="title"]')
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)

        # 슬라이드 이미지 추출
        slide_frames = soup.select('div.slide, div[class*="slide-"]')

        for i, frame in enumerate(slide_frames):
            img = frame.select_one('img')
            if img:
                src = img.get('data-src') or img.get('src', '')
                if src:
                    result['slides'].append({
                        'index': i,
                        'image_url': src,
                        'type': 'image',
                    })

        # 대체: data 속성에서 추출
        if not result['slides']:
            deck_elem = soup.select_one('[data-slides]')
            if deck_elem:
                slides_data = deck_elem.get('data-slides', '')
                urls = re.findall(r'https?://[^"\']+\.(?:jpg|png|jpeg)[^"\']*', slides_data)
                for i, url in enumerate(urls):
                    result['slides'].append({
                        'index': i,
                        'image_url': url,
                        'type': 'image',
                    })

        return result


class GenericExtractor(SlideExtractor):
    """일반 웹페이지에서 슬라이드 추출 시도"""

    def extract(self) -> dict:
        soup = self._get_page(self.url)

        result = {
            'title': '',
            'slides': [],
            'metadata': {
                'source': 'generic',
                'url': self.url,
            }
        }

        # 제목
        title = soup.find('title')
        if title:
            result['title'] = title.get_text(strip=True)

        # 이미지 기반 슬라이드 찾기
        # 슬라이드 비율 (16:9, 4:3)에 가까운 이미지 찾기
        images = soup.find_all('img')

        for i, img in enumerate(images):
            src = img.get('src', '')
            if not src:
                continue

            # 절대 URL로 변환
            if not src.startswith('http'):
                src = urljoin(self.url, src)

            # 슬라이드 관련 키워드 확인
            alt = img.get('alt', '').lower()
            classes = ' '.join(img.get('class', [])).lower()

            is_slide = any(kw in alt or kw in classes or kw in src.lower()
                          for kw in ['slide', 'page', 'deck', 'presentation'])

            if is_slide or i < 20:  # 처음 20개 이미지 포함
                result['slides'].append({
                    'index': i,
                    'image_url': src,
                    'type': 'image',
                })

        return result


def get_extractor(url: str) -> SlideExtractor:
    """URL에 맞는 추출기 반환"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if 'slideshare' in domain:
        return SlideShareExtractor(url)
    elif 'speakerdeck' in domain:
        return SpeakerDeckExtractor(url)
    else:
        return GenericExtractor(url)


def analyze_layout(slides: list) -> dict:
    """슬라이드 레이아웃 분석"""
    analysis = {
        'total_slides': len(slides),
        'patterns': [],
        'suggested_category': 'general',
    }

    if not slides:
        return analysis

    # 슬라이드 수에 따른 카테고리 추천
    count = len(slides)
    if count <= 3:
        analysis['suggested_category'] = 'cover'
    elif count <= 6:
        analysis['suggested_category'] = 'overview'
    elif count <= 10:
        analysis['suggested_category'] = 'content'
    else:
        analysis['suggested_category'] = 'presentation'

    return analysis


def generate_content_template(
    template_id: str,
    name: str,
    category: str,
    slide_data: dict,
    analysis: dict
) -> dict:
    """콘텐츠 템플릿 YAML 데이터 생성"""
    template = {
        'template': {
            'id': template_id,
            'name': name,
            'category': category,
            'source': {
                'type': slide_data['metadata'].get('source', 'unknown'),
                'url': slide_data['metadata'].get('url', ''),
                'title': slide_data.get('title', ''),
            },
            'created': datetime.now().strftime('%Y-%m-%d'),
        },
        'structure': {
            'type': 'custom',
            'description': f'{len(slide_data["slides"])}개 슬라이드 패턴',
        },
        'slides': [],
    }

    # 슬라이드 정보 추가
    for i, slide in enumerate(slide_data['slides'][:10]):  # 최대 10개
        slide_entry = {
            'index': i,
            'type': 'content',
        }
        if slide.get('image_url'):
            slide_entry['reference_image'] = slide['image_url']
        template['slides'].append(slide_entry)

    # 사용 가이드
    template['usage'] = {
        'keywords': [category, 'custom', template_id],
        'use_for': f'{category} 유형의 슬라이드 생성',
        'notes': '원본 슬라이드를 참고하여 레이아웃 구성',
    }

    return template


def update_registry(template_id: str, name: str, category: str, file_name: str) -> None:
    """레지스트리 업데이트"""
    registry = load_registry(REGISTRY_PATH, ['templates'])
    templates = registry.get('templates', [])

    # 기존 항목 확인
    existing_ids = [t['id'] for t in templates]

    entry = {
        'id': template_id,
        'name': name,
        'category': category,
        'file': file_name,
        'source': 'crawled',
        'created': datetime.now().strftime('%Y-%m-%d'),
    }

    if template_id in existing_ids:
        # 업데이트
        for i, t in enumerate(templates):
            if t['id'] == template_id:
                templates[i] = entry
                break
    else:
        # 추가
        templates.append(entry)

    registry['templates'] = templates
    save_registry(REGISTRY_PATH, registry, '콘텐츠 템플릿 레지스트리')


def cmd_crawl(args) -> int:
    """슬라이드 크롤링 실행"""
    url = args.url
    template_id = args.output
    category = args.category
    analyze_only = args.analyze_only
    name = args.name

    print(f"슬라이드 크롤러")
    print(f"=" * 50)
    print(f"URL: {url}")

    # 추출기 선택
    extractor = get_extractor(url)
    print(f"추출기: {type(extractor).__name__}")
    print()

    # 슬라이드 추출
    print("[1/4] 슬라이드 추출...")
    try:
        slide_data = extractor.extract()
    except Exception as e:
        print(f"Error: 추출 실패 - {e}")
        return 1

    slide_count = len(slide_data.get('slides', []))
    print(f"  제목: {slide_data.get('title', '(없음)')}")
    print(f"  슬라이드: {slide_count}개")

    if slide_count == 0:
        print("\nWarning: 슬라이드를 찾을 수 없습니다.")
        print("  - URL이 올바른지 확인하세요")
        print("  - 로그인이 필요한 콘텐츠일 수 있습니다")
        return 1

    # 레이아웃 분석
    print("\n[2/4] 레이아웃 분석...")
    analysis = analyze_layout(slide_data['slides'])
    print(f"  추천 카테고리: {analysis['suggested_category']}")

    # 카테고리 설정
    if not category:
        category = analysis['suggested_category']
    print(f"  사용 카테고리: {category}")

    # 분석만 모드
    if analyze_only:
        print("\n--- 분석 결과 ---")
        print(f"Title: {slide_data.get('title')}")
        print(f"Slides: {slide_count}")
        print(f"Source: {slide_data['metadata'].get('source')}")
        print(f"Category: {category}")
        print("\n슬라이드 목록:")
        for slide in slide_data['slides'][:10]:
            print(f"  [{slide['index']}] {slide.get('image_url', '')[:60]}...")
        return 0

    # 템플릿 ID 확인
    if not template_id:
        print("Error: --output 옵션으로 템플릿 ID를 지정해주세요")
        return 1

    # 템플릿 이름
    if not name:
        name = slide_data.get('title') or template_id

    # 템플릿 생성
    print("\n[3/4] 템플릿 생성...")
    template = generate_content_template(
        template_id, name, category, slide_data, analysis
    )

    # 파일 저장
    templates_dir = CONTENTS_DIR / 'templates'
    templates_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{template_id}.yaml"
    file_path = templates_dir / file_name

    yaml_str = f"""# {name}
# 크롤링 소스: {url}
# 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}

"""
    yaml_str += yaml.dump(template, allow_unicode=True, default_flow_style=False, sort_keys=False)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(yaml_str)
    print(f"  저장: {file_path}")

    # 레지스트리 업데이트
    print("\n[4/4] 레지스트리 업데이트...")
    update_registry(template_id, name, category, file_name)
    print(f"  registry.yaml 업데이트됨")

    print("\n" + "=" * 50)
    print("완료!")
    print(f"  템플릿 ID: {template_id}")
    print(f"  파일: {file_path}")
    print(f"  카테고리: {category}")

    return 0


def main():
    if not HAS_REQUESTS:
        print("Error: requests가 필요합니다.")
        print("  pip install requests")
        return 1

    if not HAS_BS4:
        print("Error: beautifulsoup4가 필요합니다.")
        print("  pip install beautifulsoup4")
        return 1

    parser = argparse.ArgumentParser(
        description='온라인 슬라이드 크롤러',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # SlideShare에서 크롤링
  python slide-crawler.py "https://www.slideshare.net/user/deck" --output my-template

  # 카테고리 지정
  python slide-crawler.py "https://speakerdeck.com/user/deck" --output timeline2 --category timeline

  # 분석만
  python slide-crawler.py "https://slideshare.net/..." --analyze-only

Supported sites:
  - SlideShare (slideshare.net)
  - Speaker Deck (speakerdeck.com)
  - 기타 웹페이지 (이미지 기반 추출)
        """
    )

    parser.add_argument('url', help='슬라이드 URL')
    parser.add_argument('--output', '-o', help='템플릿 ID')
    parser.add_argument('--name', '-n', help='템플릿 이름')
    parser.add_argument('--category', '-c', help='카테고리 (cover, timeline, process 등)')
    parser.add_argument('--analyze-only', action='store_true',
                        help='분석만 수행 (저장 안함)')

    args = parser.parse_args()
    return cmd_crawl(args)


if __name__ == '__main__':
    sys.exit(main())
