#!/usr/bin/env python3
"""
Content Creator.

라이브러리 기반 콘텐츠 템플릿 동적 생성.
Chart.js, Mermaid, ApexCharts 등을 사용하여 콘텐츠 템플릿을 생성합니다.

Usage:
    python content_creator.py --library chartjs --type bar --name sales-chart
    python content_creator.py --library mermaid --type flowchart --name process-flow
"""

import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 스크립트 디렉토리를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared.yaml_utils import save_yaml


# 라이브러리 정보
LIBRARY_INFO = {
    'chartjs': {
        'name': 'Chart.js',
        'cdn': 'https://cdn.jsdelivr.net/npm/chart.js',
        'types': ['bar', 'pie', 'line', 'doughnut', 'radar'],
        'category': 'chart',
    },
    'mermaid': {
        'name': 'Mermaid',
        'cdn': 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js',
        'types': ['flowchart', 'sequence', 'class', 'state', 'er'],
        'category': 'diagram',
    },
    'apexcharts': {
        'name': 'ApexCharts',
        'cdn': 'https://cdn.jsdelivr.net/npm/apexcharts',
        'types': ['dashboard', 'area', 'radial'],
        'category': 'chart',
    },
    'lucide': {
        'name': 'Lucide Icons',
        'cdn': 'https://unpkg.com/lucide@latest',
        'types': ['icon-grid', 'icon-list'],
        'category': 'icon',
    },
}


@dataclass
class TemplateConfig:
    """템플릿 설정."""
    library: str
    template_type: str
    name: str
    category: Optional[str] = None
    theme_mode: str = 'light'  # light | dark


class ContentCreator:
    """라이브러리 기반 콘텐츠 템플릿 생성기."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Args:
            templates_dir: 템플릿 루트 디렉토리 (기본: ppt-gen/templates)
        """
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = SCRIPT_DIR.parent.parent.parent / 'templates'

        self.contents_dir = self.templates_dir / 'contents'
        self.lib_templates_dir = SCRIPT_DIR / 'templates'

    def create(self, config: TemplateConfig) -> Optional[Path]:
        """
        라이브러리 템플릿 생성.

        Args:
            config: 템플릿 설정

        Returns:
            생성된 템플릿 디렉토리 경로
        """
        # 라이브러리 검증
        if config.library not in LIBRARY_INFO:
            print(f"Error: 지원하지 않는 라이브러리: {config.library}")
            print(f"지원 라이브러리: {', '.join(LIBRARY_INFO.keys())}")
            return None

        lib_info = LIBRARY_INFO[config.library]

        # 타입 검증
        if config.template_type not in lib_info['types']:
            print(f"Error: {config.library}에서 지원하지 않는 타입: {config.template_type}")
            print(f"지원 타입: {', '.join(lib_info['types'])}")
            return None

        # 카테고리 결정
        category = config.category or lib_info['category']

        # 출력 디렉토리
        output_dir = self.contents_dir / category / config.name
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n콘텐츠 템플릿 생성: {config.name}")
        print(f"  라이브러리: {lib_info['name']}")
        print(f"  타입: {config.template_type}")
        print(f"  카테고리: {category}")
        print(f"  출력: {output_dir}")

        try:
            # 1. template.yaml 생성
            self._create_yaml(config, lib_info, category, output_dir)

            # 2. template.html 생성
            self._create_html(config, lib_info, output_dir)

            # 3. example.html 생성 (미리보기용)
            self._create_example_html(config, lib_info, output_dir)

            # 4. 레지스트리 업데이트
            self._update_registry(config.name, category, output_dir)

            print(f"\n완료: {output_dir}")
            return output_dir

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_yaml(
        self,
        config: TemplateConfig,
        lib_info: Dict,
        category: str,
        output_dir: Path
    ) -> None:
        """template.yaml 생성."""
        # 스키마 및 예시 데이터 생성
        schema, example = self._get_schema_and_example(config.library, config.template_type)

        yaml_data = {
            'id': config.name,
            'category': category,
            'pattern': f'{config.library}-{config.template_type}',
            'description': f'{lib_info["name"]} {config.template_type} 템플릿',
            'has_ooxml': False,
            'render_method': 'library',
            'library': {
                'name': lib_info['name'],
                'cdn': lib_info['cdn'],
                'type': config.template_type,
            },
            'theme': {
                'mode': config.theme_mode,
            },
            'schema': schema,
            'example': example,
        }

        yaml_path = output_dir / 'template.yaml'
        header = f"콘텐츠 템플릿: {config.name}\n라이브러리: {lib_info['name']}"
        save_yaml(yaml_data, yaml_path, header=header)
        print(f"  YAML: template.yaml")

    def _create_html(
        self,
        config: TemplateConfig,
        lib_info: Dict,
        output_dir: Path
    ) -> None:
        """template.html 생성 (Handlebars 템플릿)."""
        html_content = self._get_html_template(config.library, config.template_type)
        html_path = output_dir / 'template.html'
        html_path.write_text(html_content, encoding='utf-8')
        print(f"  HTML: template.html")

    def _create_example_html(
        self,
        config: TemplateConfig,
        lib_info: Dict,
        output_dir: Path
    ) -> None:
        """example.html 생성 (미리보기용 완전한 HTML)."""
        example_content = self._get_example_html(config.library, config.template_type)
        example_path = output_dir / 'example.html'
        example_path.write_text(example_content, encoding='utf-8')
        print(f"  예시: example.html")

    def _update_registry(self, name: str, category: str, output_dir: Path) -> None:
        """레지스트리 업데이트."""
        try:
            from scripts.registry_manager import RegistryManager
            manager = RegistryManager()
            manager.update_content(output_dir)
            print(f"  레지스트리: 업데이트됨")
        except Exception as e:
            print(f"  레지스트리: 스킵 ({e})")

    def _get_schema_and_example(self, library: str, template_type: str) -> tuple:
        """라이브러리/타입별 스키마와 예시 데이터 반환."""
        schemas = {
            ('chartjs', 'bar'): (
                {
                    'title': 'string',
                    'labels': ['string'],
                    'datasets': [{
                        'label': 'string',
                        'data': ['number'],
                        'backgroundColor': 'string',
                    }],
                },
                {
                    'title': '월별 매출 현황',
                    'labels': ['1월', '2월', '3월', '4월', '5월', '6월'],
                    'datasets': [{
                        'label': '2024년',
                        'data': [120, 150, 180, 140, 200, 190],
                        'backgroundColor': '#3b82f6',
                    }, {
                        'label': '2025년',
                        'data': [140, 170, 200, 160, 220, 210],
                        'backgroundColor': '#10b981',
                    }],
                }
            ),
            ('chartjs', 'pie'): (
                {
                    'title': 'string',
                    'labels': ['string'],
                    'data': ['number'],
                    'backgroundColor': ['string'],
                },
                {
                    'title': '시장 점유율',
                    'labels': ['제품 A', '제품 B', '제품 C', '제품 D'],
                    'data': [35, 25, 22, 18],
                    'backgroundColor': ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'],
                }
            ),
            ('chartjs', 'line'): (
                {
                    'title': 'string',
                    'labels': ['string'],
                    'datasets': [{
                        'label': 'string',
                        'data': ['number'],
                        'borderColor': 'string',
                        'tension': 'number',
                    }],
                },
                {
                    'title': '성장 추이',
                    'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
                    'datasets': [{
                        'label': '매출',
                        'data': [100, 120, 145, 180],
                        'borderColor': '#3b82f6',
                        'tension': 0.3,
                    }, {
                        'label': '이익',
                        'data': [30, 40, 55, 70],
                        'borderColor': '#10b981',
                        'tension': 0.3,
                    }],
                }
            ),
            ('mermaid', 'flowchart'): (
                {
                    'title': 'string',
                    'direction': 'TB | LR | BT | RL',
                    'nodes': [{
                        'id': 'string',
                        'label': 'string',
                        'shape': 'rect | rounded | circle | diamond',
                    }],
                    'edges': [{
                        'from': 'string',
                        'to': 'string',
                        'label': 'string?',
                    }],
                },
                {
                    'title': '주문 처리 프로세스',
                    'direction': 'TB',
                    'nodes': [
                        {'id': 'A', 'label': '주문 접수', 'shape': 'rounded'},
                        {'id': 'B', 'label': '재고 확인', 'shape': 'diamond'},
                        {'id': 'C', 'label': '결제 처리', 'shape': 'rect'},
                        {'id': 'D', 'label': '배송 준비', 'shape': 'rect'},
                        {'id': 'E', 'label': '완료', 'shape': 'circle'},
                    ],
                    'edges': [
                        {'from': 'A', 'to': 'B'},
                        {'from': 'B', 'to': 'C', 'label': '재고 있음'},
                        {'from': 'C', 'to': 'D'},
                        {'from': 'D', 'to': 'E'},
                    ],
                }
            ),
            ('mermaid', 'sequence'): (
                {
                    'title': 'string',
                    'participants': ['string'],
                    'messages': [{
                        'from': 'string',
                        'to': 'string',
                        'message': 'string',
                        'type': 'sync | async | return',
                    }],
                },
                {
                    'title': 'API 호출 시퀀스',
                    'participants': ['Client', 'API Gateway', 'Auth Service', 'Database'],
                    'messages': [
                        {'from': 'Client', 'to': 'API Gateway', 'message': 'Request', 'type': 'sync'},
                        {'from': 'API Gateway', 'to': 'Auth Service', 'message': 'Validate Token', 'type': 'sync'},
                        {'from': 'Auth Service', 'to': 'Database', 'message': 'Query User', 'type': 'sync'},
                        {'from': 'Database', 'to': 'Auth Service', 'message': 'User Data', 'type': 'return'},
                        {'from': 'Auth Service', 'to': 'API Gateway', 'message': 'Token Valid', 'type': 'return'},
                        {'from': 'API Gateway', 'to': 'Client', 'message': 'Response', 'type': 'return'},
                    ],
                }
            ),
        }

        return schemas.get((library, template_type), ({}, {}))

    def _get_html_template(self, library: str, template_type: str) -> str:
        """라이브러리/타입별 Handlebars HTML 템플릿 반환."""
        templates = {
            ('chartjs', 'bar'): self._chartjs_bar_template(),
            ('chartjs', 'pie'): self._chartjs_pie_template(),
            ('chartjs', 'line'): self._chartjs_line_template(),
            ('mermaid', 'flowchart'): self._mermaid_flowchart_template(),
            ('mermaid', 'sequence'): self._mermaid_sequence_template(),
        }

        return templates.get((library, template_type), self._default_template())

    def _get_example_html(self, library: str, template_type: str) -> str:
        """예시 데이터가 포함된 완전한 HTML 반환."""
        examples = {
            ('chartjs', 'bar'): self._chartjs_bar_example(),
            ('chartjs', 'pie'): self._chartjs_pie_example(),
            ('chartjs', 'line'): self._chartjs_line_example(),
            ('mermaid', 'flowchart'): self._mermaid_flowchart_example(),
            ('mermaid', 'sequence'): self._mermaid_sequence_example(),
        }

        return examples.get((library, template_type), self._default_example())

    # =====================
    # Chart.js 템플릿
    # =====================

    def _chartjs_bar_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{{title}}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --background: {{theme.background}};
            --text: {{theme.text}};
        }
        .slide {
            width: 1920px;
            height: 1080px;
            background: var(--background, #ffffff);
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: var(--text, #1e293b);
            margin-bottom: 40px;
        }
        .chart-container {
            width: 100%;
            height: 800px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">{{title}}</h1>
        <div class="chart-container">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: {{{json labels}}},
                datasets: {{{json datasets}}}
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' }
                }
            }
        });
    </script>
</body>
</html>'''

    def _chartjs_bar_example(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>월별 매출 현황</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .slide {
            width: 1920px;
            height: 1080px;
            background: #ffffff;
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 40px;
        }
        .chart-container {
            width: 100%;
            height: 800px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">월별 매출 현황</h1>
        <div class="chart-container">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['1월', '2월', '3월', '4월', '5월', '6월'],
                datasets: [{
                    label: '2024년',
                    data: [120, 150, 180, 140, 200, 190],
                    backgroundColor: '#3b82f6'
                }, {
                    label: '2025년',
                    data: [140, 170, 200, 160, 220, 210],
                    backgroundColor: '#10b981'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' }
                }
            }
        });
    </script>
</body>
</html>'''

    def _chartjs_pie_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{{title}}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .slide {
            width: 1920px;
            height: 1080px;
            background: {{theme.background}};
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: {{theme.text}};
            margin-bottom: 40px;
        }
        .chart-container {
            width: 800px;
            height: 800px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">{{title}}</h1>
        <div class="chart-container">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: {{{json labels}}},
                datasets: [{
                    data: {{{json data}}},
                    backgroundColor: {{{json backgroundColor}}}
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right' }
                }
            }
        });
    </script>
</body>
</html>'''

    def _chartjs_pie_example(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>시장 점유율</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .slide {
            width: 1920px;
            height: 1080px;
            background: #ffffff;
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 40px;
        }
        .chart-container {
            width: 800px;
            height: 800px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">시장 점유율</h1>
        <div class="chart-container">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['제품 A', '제품 B', '제품 C', '제품 D'],
                datasets: [{
                    data: [35, 25, 22, 18],
                    backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right' }
                }
            }
        });
    </script>
</body>
</html>'''

    def _chartjs_line_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{{title}}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .slide {
            width: 1920px;
            height: 1080px;
            background: {{theme.background}};
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: {{theme.text}};
            margin-bottom: 40px;
        }
        .chart-container {
            width: 100%;
            height: 800px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">{{title}}</h1>
        <div class="chart-container">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{{json labels}}},
                datasets: {{{json datasets}}}
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' }
                }
            }
        });
    </script>
</body>
</html>'''

    def _chartjs_line_example(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>성장 추이</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .slide {
            width: 1920px;
            height: 1080px;
            background: #ffffff;
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 40px;
        }
        .chart-container {
            width: 100%;
            height: 800px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">성장 추이</h1>
        <div class="chart-container">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Q1', 'Q2', 'Q3', 'Q4'],
                datasets: [{
                    label: '매출',
                    data: [100, 120, 145, 180],
                    borderColor: '#3b82f6',
                    tension: 0.3
                }, {
                    label: '이익',
                    data: [30, 40, 55, 70],
                    borderColor: '#10b981',
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' }
                }
            }
        });
    </script>
</body>
</html>'''

    # =====================
    # Mermaid 템플릿
    # =====================

    def _mermaid_flowchart_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{{title}}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        .slide {
            width: 1920px;
            height: 1080px;
            background: {{theme.background}};
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: {{theme.text}};
            margin-bottom: 40px;
        }
        .mermaid {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 800px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">{{title}}</h1>
        <div class="mermaid">
            flowchart {{direction}}
            {{#each nodes}}
            {{id}}{{#if (eq shape "rounded")}}({{label}}){{else if (eq shape "diamond")}}{{"{"}}{{label}}{{"}"}}{{else if (eq shape "circle")}}(({{label}})){{else}}[{{label}}]{{/if}}
            {{/each}}
            {{#each edges}}
            {{from}} -->{{#if label}}|{{label}}|{{/if}} {{to}}
            {{/each}}
        </div>
    </div>
    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'default' });
    </script>
</body>
</html>'''

    def _mermaid_flowchart_example(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>주문 처리 프로세스</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        .slide {
            width: 1920px;
            height: 1080px;
            background: #ffffff;
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 40px;
        }
        .mermaid {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 800px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">주문 처리 프로세스</h1>
        <div class="mermaid">
            flowchart TB
            A(주문 접수)
            B{재고 확인}
            C[결제 처리]
            D[배송 준비]
            E((완료))
            A --> B
            B -->|재고 있음| C
            C --> D
            D --> E
        </div>
    </div>
    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'default' });
    </script>
</body>
</html>'''

    def _mermaid_sequence_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{{title}}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        .slide {
            width: 1920px;
            height: 1080px;
            background: {{theme.background}};
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: {{theme.text}};
            margin-bottom: 40px;
        }
        .mermaid {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 800px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">{{title}}</h1>
        <div class="mermaid">
            sequenceDiagram
            {{#each participants}}
            participant {{this}}
            {{/each}}
            {{#each messages}}
            {{from}}{{#if (eq type "sync")}}->>{{else if (eq type "async")}}-->>{{else}}-->>{{/if}}{{to}}: {{message}}
            {{/each}}
        </div>
    </div>
    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'default' });
    </script>
</body>
</html>'''

    def _mermaid_sequence_example(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>API 호출 시퀀스</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        .slide {
            width: 1920px;
            height: 1080px;
            background: #ffffff;
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 40px;
        }
        .mermaid {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 800px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">API 호출 시퀀스</h1>
        <div class="mermaid">
            sequenceDiagram
            participant Client
            participant API Gateway
            participant Auth Service
            participant Database
            Client->>API Gateway: Request
            API Gateway->>Auth Service: Validate Token
            Auth Service->>Database: Query User
            Database-->>Auth Service: User Data
            Auth Service-->>API Gateway: Token Valid
            API Gateway-->>Client: Response
        </div>
    </div>
    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'default' });
    </script>
</body>
</html>'''

    def _default_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{{title}}</title>
    <style>
        .slide {
            width: 1920px;
            height: 1080px;
            background: #ffffff;
            padding: 60px;
            font-family: 'Pretendard', sans-serif;
        }
        .title {
            font-size: 48px;
            font-weight: 700;
            color: #1e293b;
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="title">{{title}}</h1>
        <p>템플릿 내용</p>
    </div>
</body>
</html>'''

    def _default_example(self) -> str:
        return self._default_template().replace('{{title}}', '기본 템플릿')

    def list_libraries(self) -> None:
        """지원 라이브러리 목록 출력."""
        print("\n=== 지원 라이브러리 ===")
        for lib_id, info in LIBRARY_INFO.items():
            print(f"\n{info['name']} ({lib_id})")
            print(f"  CDN: {info['cdn']}")
            print(f"  타입: {', '.join(info['types'])}")
            print(f"  카테고리: {info['category']}")


def main():
    """CLI 엔트리포인트."""
    import argparse

    parser = argparse.ArgumentParser(
        description="라이브러리 기반 콘텐츠 템플릿 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python content_creator.py --library chartjs --type bar --name sales-chart
    python content_creator.py --library mermaid --type flowchart --name process-flow
    python content_creator.py --list
        """
    )

    parser.add_argument(
        '--library', '-l',
        choices=list(LIBRARY_INFO.keys()),
        help='라이브러리 선택'
    )
    parser.add_argument(
        '--type', '-t',
        help='템플릿 타입'
    )
    parser.add_argument(
        '--name', '-n',
        help='템플릿 이름 (케밥케이스)'
    )
    parser.add_argument(
        '--category', '-c',
        help='카테고리 (기본: 라이브러리 기본값)'
    )
    parser.add_argument(
        '--theme',
        choices=['light', 'dark'],
        default='light',
        help='테마 모드'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='지원 라이브러리 목록 출력'
    )

    args = parser.parse_args()

    creator = ContentCreator()

    if args.list:
        creator.list_libraries()
        return 0

    if not args.library or not args.type or not args.name:
        parser.print_help()
        print("\n--library, --type, --name 옵션이 필수입니다.")
        return 1

    config = TemplateConfig(
        library=args.library,
        template_type=args.type,
        name=args.name,
        category=args.category,
        theme_mode=args.theme
    )

    result = creator.create(config)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
