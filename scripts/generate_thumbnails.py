#!/usr/bin/env python3
"""
PowerPoint 슬라이드 썸네일 생성 스크립트

사용법:
    python scripts/generate_thumbnails.py <input.pptx> <output_dir>

예시:
    python scripts/generate_thumbnails.py ppt-sample/동국시스템즈-템플릿.pptx /tmp/dongkuk-thumbnails
"""

import sys
import os
from pathlib import Path

def generate_thumbnails_with_pptxtoimages(input_path: str, output_dir: str):
    """
    pptxtoimages 라이브러리를 사용하여 썸네일 생성
    """
    try:
        from pptxtoimages import pptxtoimages
    except ImportError:
        print("오류: pptxtoimages 라이브러리가 설치되지 않았습니다.")
        print("설치 명령: pip install pptxtoimages")
        sys.exit(1)

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    print(f"입력 파일: {input_path}")
    print(f"출력 디렉토리: {output_dir}")

    # 썸네일 생성
    # pptxtoimages는 모든 슬라이드를 이미지로 변환
    image_paths = pptxtoimages(input_path, output_dir)

    # 생성된 이미지를 slide-{n}.png 형식으로 정리
    generated_files = []
    for idx, img_path in enumerate(sorted(image_paths)):
        new_name = f"slide-{idx}.png"
        new_path = os.path.join(output_dir, new_name)

        # 이미지 이동 또는 이름 변경
        if os.path.abspath(img_path) != os.path.abspath(new_path):
            os.rename(img_path, new_path)

        generated_files.append(new_path)
        print(f"생성됨: {new_name}")

    print(f"\n총 {len(generated_files)}개 슬라이드 썸네일 생성 완료")
    return generated_files


def generate_thumbnails_with_libreoffice(input_path: str, output_dir: str):
    """
    LibreOffice headless 모드를 사용하여 썸네일 생성
    (대안: pptxtoimages가 작동하지 않을 경우)
    """
    import subprocess
    import tempfile
    from pdf2image import convert_from_path

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    print(f"입력 파일: {input_path}")
    print(f"출력 디렉토리: {output_dir}")

    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. PPTX를 PDF로 변환
        pdf_path = os.path.join(tmpdir, "temp.pdf")
        print("LibreOffice로 PDF 변환 중...")

        subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", tmpdir,
            input_path
        ], check=True)

        # 2. PDF를 이미지로 변환
        print("PDF를 PNG로 변환 중...")
        images = convert_from_path(pdf_path, dpi=150)

        # 3. 이미지 저장
        generated_files = []
        for idx, image in enumerate(images):
            output_path = os.path.join(output_dir, f"slide-{idx}.png")
            image.save(output_path, "PNG")
            generated_files.append(output_path)
            print(f"생성됨: slide-{idx}.png")

    print(f"\n총 {len(generated_files)}개 슬라이드 썸네일 생성 완료")
    return generated_files


def main():
    if len(sys.argv) < 3:
        print("사용법: python generate_thumbnails.py <input.pptx> <output_dir>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    # 입력 파일 확인
    if not os.path.exists(input_path):
        print(f"오류: 입력 파일이 존재하지 않습니다: {input_path}")
        sys.exit(1)

    try:
        # 먼저 pptxtoimages 시도
        generate_thumbnails_with_pptxtoimages(input_path, output_dir)
    except Exception as e:
        print(f"pptxtoimages 실패: {e}")
        print("LibreOffice 방법으로 시도 중...")
        try:
            generate_thumbnails_with_libreoffice(input_path, output_dir)
        except Exception as e2:
            print(f"LibreOffice 방법도 실패: {e2}")
            sys.exit(1)


if __name__ == "__main__":
    main()
