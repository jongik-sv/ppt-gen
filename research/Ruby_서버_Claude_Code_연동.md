# Ruby 서버에서 Claude Code CLI 연동

> 웹 서버를 통해 Claude Code 스킬을 자동 실행하는 방법

## 개요

Ruby 웹 서버(Sinatra/Rails)에서 파일 업로드나 버튼 클릭 시 Claude Code CLI를 실행하여 `ppt-extract`, `ppt-gen` 등의 스킬을 자동으로 트리거할 수 있다.

## 핵심 구현

### 1. 파일 업로드 → ppt-extract 실행

```ruby
require 'sinatra'
require 'open3'
require 'json'
require 'fileutils'

post '/extract' do
  content_type :json

  # 파일 저장
  file = params[:file][:tempfile]
  filename = params[:file][:filename]
  upload_path = "./uploads/#{filename}"
  FileUtils.cp(file.path, upload_path)

  # Claude Code 실행 (비대화형 모드)
  prompt = "/ppt-extract #{upload_path}"
  stdout, stderr, status = Open3.capture3(
    "claude", "-p", prompt, "--print",
    chdir: "/home/jji/project/ppt-gen"
  )

  {
    success: status.success?,
    output: stdout,
    error: stderr
  }.to_json
end
```

### 2. 버튼 클릭 → ppt-gen 실행 (백그라운드)

```ruby
post '/generate' do
  content_type :json

  topic = params[:topic]
  template = params[:template] || 'default'

  prompt = "/ppt-gen #{topic} --template #{template}"

  # 장시간 작업은 백그라운드로
  pid = spawn(
    "claude", "-p", prompt, "--print",
    chdir: "/home/jji/project/ppt-gen",
    out: "logs/gen_#{Time.now.to_i}.log",
    err: "logs/gen_#{Time.now.to_i}.err"
  )
  Process.detach(pid)

  { job_id: pid, status: 'started' }.to_json
end

# 작업 상태 확인
get '/status/:job_id' do
  # 프로세스 상태 확인 로직
end
```

### 3. 실시간 스트리밍 (SSE)

```ruby
require 'sinatra'

get '/generate/stream', provides: 'text/event-stream' do
  stream(:keep_open) do |out|
    topic = params[:topic]

    IO.popen(["claude", "-p", "/ppt-gen #{topic}", "--print"],
             chdir: "/home/jji/project/ppt-gen") do |io|
      io.each_line do |line|
        out << "data: #{line.to_json}\n\n"
      end
    end

    out << "event: done\ndata: {}\n\n"
  end
end
```

## 프론트엔드 예시

```html
<!-- 파일 업로드 -->
<form id="extractForm">
  <input type="file" name="file" accept=".pptx">
  <button type="submit">추출 시작</button>
</form>

<!-- PPT 생성 -->
<button onclick="generatePPT()">PPT 생성</button>
<pre id="output"></pre>

<script>
// 스트리밍으로 실시간 출력 표시
function generatePPT() {
  const output = document.getElementById('output');
  const eventSource = new EventSource('/generate/stream?topic=프로젝트계획서');

  eventSource.onmessage = (e) => {
    output.textContent += JSON.parse(e.data);
  };

  eventSource.addEventListener('done', () => {
    eventSource.close();
  });
}
</script>
```

## 주요 고려사항

| 항목 | 권장 방식 |
|------|----------|
| 장시간 작업 | 백그라운드 프로세스 + 상태 폴링 또는 SSE |
| 동시 실행 제한 | 큐 시스템 (Sidekiq, Resque) |
| 인증 | API 키 또는 세션 기반 |
| 타임아웃 | `Timeout.timeout(300)` 등 |

## 보안 주의사항

```ruby
require 'shellwords'

# 사용자 입력은 반드시 이스케이프
safe_input = Shellwords.escape(user_input)
```

## 관련 링크

- [Claude Code CLI 문서](https://docs.anthropic.com/claude-code)
- [Sinatra 공식 문서](http://sinatrarb.com/)
