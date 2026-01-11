#!/usr/bin/env python3
"""
Font Manager - 폰트 가용성 검사 및 자동 다운로드

기능:
- 시스템 폰트 가용성 검사
- Google Fonts에서 대체 폰트 자동 다운로드
- 폰트 매핑 관리 (상용 → 무료 대체)

Usage:
    from font_manager import FontManager

    fm = FontManager()
    fm.check_and_install("본고딕 Medium")  # 없으면 Noto Sans KR 다운로드
"""

import os
import sys
import tempfile
import zipfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
import yaml


class FontManager:
    """폰트 가용성 검사 및 다운로드 관리"""

    GOOGLE_FONTS_API = "https://fonts.google.com/download?family="

    # 기본 폰트 매핑 (상용 폰트 → Google Fonts 대체)
    DEFAULT_MAPPINGS = {
        # 본고딕 계열
        "본고딕": "Noto Sans KR",
        "본고딕 Medium": "Noto Sans KR",
        "본고딕 Normal": "Noto Sans KR",
        "본고딕 Bold": "Noto Sans KR",
        "본고딕 Light": "Noto Sans KR",

        # 본명조 계열
        "본명조": "Noto Serif KR",
        "본명조 Regular": "Noto Serif KR",

        # 산돌 계열
        "산돌고딕": "Noto Sans KR",
        "산돌고딕 Neo": "Noto Sans KR",

        # 시스템 폰트
        "맑은 고딕": "Noto Sans KR",
        "Malgun Gothic": "Noto Sans KR",
        "굴림": "Noto Sans KR",
        "Gulim": "Noto Sans KR",
        "바탕": "Noto Serif KR",
        "Batang": "Noto Serif KR",
        "돋움": "Noto Sans KR",
        "Dotum": "Noto Sans KR",

        # 나눔 계열 (Google Fonts에서 직접 제공)
        "나눔고딕": "Nanum Gothic",
        "NanumGothic": "Nanum Gothic",
        "나눔명조": "Nanum Myeongjo",
        "NanumMyeongjo": "Nanum Myeongjo",
        "나눔바른고딕": "Nanum Gothic",

        # 영문 폰트
        "Arial": "Roboto",
        "Helvetica": "Roboto",
        "Times New Roman": "Roboto Serif",
    }

    # Google Fonts 다운로드 가능 목록
    GOOGLE_FONTS = {
        "Noto Sans KR": {
            "weights": [100, 300, 400, 500, 700, 900],
            "category": "sans-serif",
        },
        "Noto Serif KR": {
            "weights": [200, 300, 400, 500, 600, 700, 900],
            "category": "serif",
        },
        "Nanum Gothic": {
            "weights": [400, 700, 800],
            "category": "sans-serif",
        },
        "Nanum Myeongjo": {
            "weights": [400, 700, 800],
            "category": "serif",
        },
        "Roboto": {
            "weights": [100, 300, 400, 500, 700, 900],
            "category": "sans-serif",
        },
        "Roboto Serif": {
            "weights": [100, 300, 400, 500, 700, 900],
            "category": "serif",
        },
    }

    def __init__(self, mappings_file: Optional[Path] = None):
        """
        Args:
            mappings_file: 커스텀 폰트 매핑 YAML 파일 경로 (선택)
        """
        self.mappings = self.DEFAULT_MAPPINGS.copy()
        self._font_cache: Optional[set] = None

        if mappings_file and Path(mappings_file).exists():
            self._load_custom_mappings(mappings_file)

    def _load_custom_mappings(self, mappings_file: Path) -> None:
        """커스텀 매핑 파일 로드"""
        try:
            with open(mappings_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'mappings' in data:
                    self.mappings.update(data['mappings'])
        except Exception as e:
            print(f"경고: 폰트 매핑 파일 로드 실패: {e}")

    def get_system_fonts(self) -> set:
        """시스템에 설치된 폰트 목록 반환 (캐싱)"""
        if self._font_cache is not None:
            return self._font_cache

        fonts = set()

        # matplotlib 사용 시도
        try:
            from matplotlib import font_manager
            fonts = {f.name for f in font_manager.fontManager.ttflist}
            self._font_cache = fonts
            return fonts
        except ImportError:
            pass

        # Windows: 레지스트리에서 폰트 읽기
        if sys.platform == 'win32':
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
                )
                i = 0
                while True:
                    try:
                        name, _, _ = winreg.EnumValue(key, i)
                        # "Arial (TrueType)" → "Arial"
                        font_name = name.split('(')[0].strip()
                        fonts.add(font_name)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except Exception:
                pass

            # 사용자 폰트 디렉토리도 확인
            user_fonts = Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts"
            if user_fonts.exists():
                for f in user_fonts.glob("*.ttf"):
                    fonts.add(f.stem)
                for f in user_fonts.glob("*.otf"):
                    fonts.add(f.stem)

        # macOS/Linux: 폰트 디렉토리 스캔
        else:
            font_dirs = [
                Path.home() / ".fonts",
                Path.home() / "Library" / "Fonts",
                Path("/usr/share/fonts"),
                Path("/usr/local/share/fonts"),
            ]
            for font_dir in font_dirs:
                if font_dir.exists():
                    for f in font_dir.rglob("*.ttf"):
                        fonts.add(f.stem)
                    for f in font_dir.rglob("*.otf"):
                        fonts.add(f.stem)

        self._font_cache = fonts
        return fonts

    def check_font_availability(self, font_name: str) -> bool:
        """폰트가 시스템에 설치되어 있는지 확인"""
        if not font_name:
            return True

        fonts = self.get_system_fonts()

        # 정확한 이름 매칭
        if font_name in fonts:
            return True

        # 대소문자 무시 매칭
        font_lower = font_name.lower()
        for f in fonts:
            if f.lower() == font_lower:
                return True

        # 부분 매칭 (폰트 이름 변형 고려)
        # 예: "Noto Sans KR" vs "NotoSansKR-Regular"
        base_name = font_name.replace(" ", "").lower()
        for f in fonts:
            if base_name in f.replace(" ", "").lower():
                return True

        return False

    def get_alternative_font(self, font_name: str) -> Optional[str]:
        """대체 폰트 이름 반환"""
        if not font_name:
            return None

        # 직접 매핑 확인
        if font_name in self.mappings:
            return self.mappings[font_name]

        # 부분 매칭 (예: "본고딕 Medium" → "본고딕"으로 매핑)
        for key, value in self.mappings.items():
            if key in font_name or font_name in key:
                return value

        return None

    def get_font_install_dir(self) -> Path:
        """OS별 사용자 폰트 설치 디렉토리 반환"""
        if sys.platform == 'win32':
            return Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts"
        elif sys.platform == 'darwin':
            return Path.home() / "Library" / "Fonts"
        else:
            return Path.home() / ".fonts"

    def download_google_font(self, font_name: str, install: bool = True) -> bool:
        """Google Fonts에서 폰트 다운로드

        Args:
            font_name: Google Fonts 폰트 이름 (예: "Noto Sans KR")
            install: True면 시스템에 설치, False면 다운로드만

        Returns:
            성공 여부
        """
        if font_name not in self.GOOGLE_FONTS:
            print(f"  경고: '{font_name}'은(는) Google Fonts에 없습니다.")
            return False

        # 이미 설치되어 있으면 스킵
        if self.check_font_availability(font_name):
            print(f"  '{font_name}' 이미 설치됨")
            return True

        url = f"{self.GOOGLE_FONTS_API}{font_name.replace(' ', '+')}"

        try:
            print(f"  '{font_name}' 다운로드 중...")

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                zip_path = tmp_path / "font.zip"

                # 다운로드
                urllib.request.urlretrieve(url, zip_path)

                # 설치 디렉토리
                install_dir = self.get_font_install_dir() if install else tmp_path / "fonts"
                install_dir.mkdir(parents=True, exist_ok=True)

                # 압축 해제
                installed_count = 0
                with zipfile.ZipFile(zip_path, 'r') as z:
                    for file in z.namelist():
                        if file.endswith(('.ttf', '.otf')):
                            # 파일명만 추출 (중첩 폴더 무시)
                            filename = Path(file).name
                            dest_path = install_dir / filename

                            with z.open(file) as src:
                                with open(dest_path, 'wb') as dst:
                                    dst.write(src.read())

                            installed_count += 1

                print(f"  ✅ '{font_name}' 설치 완료 ({installed_count}개 파일)")
                print(f"     위치: {install_dir}")

                # 캐시 초기화 (새 폰트 반영)
                self._font_cache = None

                return True

        except urllib.error.HTTPError as e:
            print(f"  ❌ 다운로드 실패 (HTTP {e.code}): {font_name}")
            return False
        except Exception as e:
            print(f"  ❌ 폰트 다운로드 실패: {e}")
            return False

    def check_and_install(self, font_name: str, auto_install: bool = True) -> dict:
        """폰트 확인 및 필요시 대체 폰트 설치

        Args:
            font_name: 확인할 폰트 이름
            auto_install: True면 자동 설치, False면 확인만

        Returns:
            {
                'original': str,        # 원본 폰트 이름
                'available': bool,      # 원본 폰트 사용 가능 여부
                'alternative': str,     # 대체 폰트 이름 (없으면 None)
                'installed': bool,      # 대체 폰트 설치 여부
                'fallback': str,        # 최종 사용할 폰트
            }
        """
        result = {
            'original': font_name,
            'available': False,
            'alternative': None,
            'installed': False,
            'fallback': font_name,
        }

        if not font_name:
            result['available'] = True
            return result

        # 1. 원본 폰트 확인
        if self.check_font_availability(font_name):
            result['available'] = True
            return result

        print(f"  ⚠️ 폰트 없음: '{font_name}'")

        # 2. 대체 폰트 찾기
        alternative = self.get_alternative_font(font_name)
        if alternative:
            result['alternative'] = alternative

            # 대체 폰트가 이미 설치되어 있는지 확인
            if self.check_font_availability(alternative):
                print(f"     대체 폰트 사용: '{alternative}'")
                result['installed'] = True
                result['fallback'] = alternative
                return result

            # 3. 자동 설치
            if auto_install:
                if self.download_google_font(alternative):
                    result['installed'] = True
                    result['fallback'] = alternative
                else:
                    result['fallback'] = "sans-serif"
            else:
                print(f"     권장 대체 폰트: '{alternative}'")
                result['fallback'] = alternative
        else:
            print(f"     대체 폰트 없음, 시스템 기본 폰트 사용")
            result['fallback'] = "sans-serif"

        return result

    def process_theme_fonts(self, theme: dict, auto_install: bool = True) -> dict:
        """테마의 폰트들을 검사하고 필요시 대체 폰트 설치

        Args:
            theme: {'fonts': {'title': '...', 'body': '...'}} 형식의 테마 dict
            auto_install: 자동 설치 여부

        Returns:
            업데이트된 테마 dict (fallback 정보 포함)
        """
        fonts = theme.get('fonts', {})
        if not fonts:
            return theme

        for font_type in ['title', 'body']:
            font_name = fonts.get(font_type)
            if font_name:
                result = self.check_and_install(font_name, auto_install)

                # fallback 정보 추가
                if not result['available']:
                    fonts[f'{font_type}_fallback'] = result['fallback']
                    fonts[f'{font_type}_original'] = result['original']

        theme['fonts'] = fonts
        return theme


def main():
    """CLI 인터페이스"""
    import argparse

    parser = argparse.ArgumentParser(description='폰트 가용성 검사 및 다운로드')
    parser.add_argument('fonts', nargs='*', help='확인할 폰트 이름들')
    parser.add_argument('--list', action='store_true', help='시스템 폰트 목록 출력')
    parser.add_argument('--no-install', action='store_true', help='자동 설치 비활성화')

    args = parser.parse_args()

    fm = FontManager()

    if args.list:
        fonts = sorted(fm.get_system_fonts())
        print(f"시스템 폰트 ({len(fonts)}개):")
        for f in fonts[:50]:  # 처음 50개만
            print(f"  {f}")
        if len(fonts) > 50:
            print(f"  ... 외 {len(fonts) - 50}개")
        return

    if args.fonts:
        for font in args.fonts:
            print(f"\n폰트 확인: {font}")
            result = fm.check_and_install(font, auto_install=not args.no_install)
            print(f"  결과: {result}")
    else:
        # 기본 테스트
        test_fonts = ["본고딕 Medium", "Noto Sans KR", "Arial"]
        print("폰트 가용성 테스트:")
        for font in test_fonts:
            available = fm.check_font_availability(font)
            alt = fm.get_alternative_font(font) if not available else None
            print(f"  {font}: {'✅' if available else '❌'} {f'→ {alt}' if alt else ''}")


if __name__ == '__main__':
    main()
