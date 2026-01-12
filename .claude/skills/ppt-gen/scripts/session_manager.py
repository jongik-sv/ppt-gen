#!/usr/bin/env python3
"""
세션 관리 모듈.
PPT 생성 파이프라인의 상태를 session.yaml로 추적.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


class SessionManager:
    """세션 생성, 읽기, 업데이트, 삭제를 관리."""

    def __init__(self, working_dir: str = "working"):
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)

    def create(self, settings: Optional[dict] = None) -> str:
        """새 세션 생성. 세션 ID 반환."""
        session_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        session_dir = self.working_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "output").mkdir(exist_ok=True)

        session_data = {
            "session": {
                "id": session_id,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
            },
            "settings": settings or {},
            "slides": [],
            "output": None,
        }

        self._save(session_id, session_data)
        return session_id

    def load(self, session_id: str) -> dict:
        """세션 데이터 로드."""
        session_file = self.working_dir / session_id / "session.yaml"
        if not session_file.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        with open(session_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def update(self, session_id: str, updates: dict) -> None:
        """세션 데이터 업데이트 (병합)."""
        data = self.load(session_id)
        self._deep_merge(data, updates)
        self._save(session_id, data)

    def update_status(self, session_id: str, status: str) -> None:
        """세션 상태 업데이트."""
        data = self.load(session_id)
        data["session"]["status"] = status
        self._save(session_id, data)

    def update_settings(self, session_id: str, settings: dict) -> None:
        """Stage 1 설정 저장."""
        data = self.load(session_id)
        data["settings"].update(settings)
        data["session"]["status"] = "configured"
        self._save(session_id, data)

    def add_slide(self, session_id: str, slide_data: dict) -> int:
        """슬라이드 추가. 인덱스 반환."""
        data = self.load(session_id)
        index = len(data["slides"]) + 1
        slide_data["index"] = index
        slide_data["status"] = slide_data.get("status", "pending")
        data["slides"].append(slide_data)
        self._save(session_id, data)
        return index

    def update_slide(self, session_id: str, index: int, updates: dict) -> None:
        """특정 슬라이드 업데이트."""
        data = self.load(session_id)
        for slide in data["slides"]:
            if slide["index"] == index:
                self._deep_merge(slide, updates)
                break
        self._save(session_id, data)

    def update_slide_status(self, session_id: str, index: int, status: str) -> None:
        """슬라이드 상태 업데이트."""
        self.update_slide(session_id, index, {"status": status})

    def add_attempt(self, session_id: str, slide_index: int, attempt_data: dict) -> int:
        """슬라이드에 시도 추가. 시도 번호 반환."""
        data = self.load(session_id)
        for slide in data["slides"]:
            if slide["index"] == slide_index:
                if "attempts" not in slide:
                    slide["attempts"] = []
                attempt_num = len(slide["attempts"]) + 1
                attempt_data["attempt"] = attempt_num
                slide["attempts"].append(attempt_data)
                self._save(session_id, data)
                return attempt_num
        raise ValueError(f"Slide {slide_index} not found")

    def set_final_attempt(self, session_id: str, slide_index: int, attempt_num: int) -> None:
        """슬라이드의 최종 시도 설정."""
        self.update_slide(session_id, slide_index, {
            "final_attempt": attempt_num,
            "status": "completed"
        })

    def set_output(self, session_id: str, file_path: str) -> None:
        """최종 출력 파일 설정."""
        data = self.load(session_id)
        data["output"] = {
            "file": file_path,
            "generated_at": datetime.now().isoformat(),
        }
        data["session"]["status"] = "completed"
        self._save(session_id, data)

    def get_session_dir(self, session_id: str) -> Path:
        """세션 디렉토리 경로 반환."""
        return self.working_dir / session_id

    def get_output_dir(self, session_id: str) -> Path:
        """세션 출력 디렉토리 경로 반환."""
        return self.working_dir / session_id / "output"

    def list_sessions(self) -> list:
        """모든 세션 목록 반환."""
        sessions = []
        for item in self.working_dir.iterdir():
            if item.is_dir() and (item / "session.yaml").exists():
                try:
                    data = self.load(item.name)
                    sessions.append({
                        "id": item.name,
                        "status": data["session"]["status"],
                        "created_at": data["session"]["created_at"],
                    })
                except Exception:
                    pass
        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)

    def delete(self, session_id: str) -> None:
        """세션 삭제."""
        import shutil
        session_dir = self.working_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)

    def _save(self, session_id: str, data: dict) -> None:
        """세션 데이터 저장."""
        session_file = self.working_dir / session_id / "session.yaml"
        with open(session_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def _deep_merge(self, base: dict, updates: dict) -> None:
        """딕셔너리 깊은 병합."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value


# CLI 사용
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="세션 관리")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    create_parser = subparsers.add_parser("create", help="새 세션 생성")
    create_parser.add_argument("--working-dir", default="working")

    # list
    list_parser = subparsers.add_parser("list", help="세션 목록")
    list_parser.add_argument("--working-dir", default="working")

    # load
    load_parser = subparsers.add_parser("load", help="세션 로드")
    load_parser.add_argument("session_id")
    load_parser.add_argument("--working-dir", default="working")

    # update-status
    status_parser = subparsers.add_parser("update-status", help="상태 업데이트")
    status_parser.add_argument("session_id")
    status_parser.add_argument("status")
    status_parser.add_argument("--working-dir", default="working")

    args = parser.parse_args()
    manager = SessionManager(args.working_dir)

    if args.command == "create":
        session_id = manager.create()
        print(session_id)
    elif args.command == "list":
        sessions = manager.list_sessions()
        print(json.dumps(sessions, indent=2, ensure_ascii=False))
    elif args.command == "load":
        data = manager.load(args.session_id)
        print(yaml.dump(data, allow_unicode=True, default_flow_style=False))
    elif args.command == "update-status":
        manager.update_status(args.session_id, args.status)
        print(f"Updated: {args.session_id} -> {args.status}")
