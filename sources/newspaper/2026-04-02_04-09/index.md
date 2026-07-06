---
title: "Vol.4 (4/2-4/9)"
date: 2026-04-09
draft: false
---

<div class="masthead"><div class="mast-title">THE WEEKLY DAEMON</div><div class="mast-meta"><span>Vol.4 2026.4/2 – 4/9</span><span>WEEKLY TECH &amp; AI DIGEST</span><span>32 Articles This Week</span></div></div>


## CLAUDE'S PICK

### CLI-Anything — GUI 소프트웨어를 AI 에이전트용 CLI로 변환

<div class="badges"><img src="../assets/badges/claude-pick.png" class="badge" alt="Claude's Pick"></div>

![CLI-Anything — GUI 소프트웨어를 AI 에이전트용 CLI로 변환](images/17.jpg)

AI 에이전트는 마우스 클릭이 불가능해 GUI 소프트웨어를 직접 조작할 수 없다는 문제가 있다. CLI-Anything은 소프트웨어의 소스 코드를 분석하여 GUI 동작을 CLI 명령어로 매핑함으로써 이를 해결한다. GIMP, Blender, LibreOffice, OBS Studio, Audacity 등 다양한 소프트웨어를 지원하며, 한 줄의 명령어로 이미지 편집, 3D 렌더링, 문서 작성, 방송 제어 등을 자동화할 수 있다. Claude Code 등 AI 코드 생성 도구와 통합되어 있으며 커뮤니티 기여로 지원 소프트웨어가 지속 확대되고 있다.

**핵심 포인트:** 핵심 성과: GitHub 스타 23,000개 달성, 7단계 파이프라인을 한 줄의 명령어로 자동 실행 가능하며 GIMP 필터 적용, 리사이즈, 내보내기 등 복잡한 작업을 터미널에서 직접 제어 가능.

🔗 [github.com/HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)

*GitHub*

### agent-skills — AI 에이전트에 개발 습관을 심는 오픈소스 스킬팩

<div class="badges"><img src="../assets/badges/claude-pick.png" class="badge" alt="Claude's Pick"></div>

![agent-skills — AI 에이전트에 개발 습관을 심는 오픈소스 스킬팩](images/10.jpg)

AI 코딩 에이전트는 빠르고 강력하지만 스펙을 건너뛰고 테스트를 무시하며 보안 리뷰를 생략하는 경향이 있다. 구글 Cloud AI 디렉터인 Addy Osmani가 오픈소스로 공개한 agent-skills는 시니어 엔지니어의 워크플로 19개를 마크다운 형식으로 구조화하여 에이전트의 개발 프로세스를 개선한다. 이는 에이전트 옆에 앉은 시니어처럼 스펙 검토, 테스트 실행, 코드 리뷰를 강제하는 방식으로 AI 에이전트의 아키텍처 의존 문제를 해결한다.

**핵심 포인트:** 핵심 기여: AI 에이전트의 성능 병목이 AI 자체가 아닌 입력된 스펙의 품질임을 인식하고, 시니어 엔지니어의 베스트 프랙티스 19개를 구조화된 형식으로 제공하여 에이전트의 생산성과 코드 품질을 동시에 향상시킨다.

🔗 [github.com/addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)

*GitHub*

### Qwen3.5 27B vs Gemma4 31B — 경량 LLM의 구조 차이가 만드는 성능 격차

<!-- badge:3 -->
![Qwen3.5 27B vs Gemma4 31B — 경량 LLM의 구조 차이가 만드는 성능 격차](images/03.jpg)

오픈소스 LLM 벤치마크에서 Google의 Gemma4 31B가 Gemini 3 Flash에 근접한 높은 성능을 보였으나, 중국의 Qwen3.5 27B가 더 적은 리소스로 더 높은 스코어를 달성하고 있다. 이 차이는 모델 구조의 차이에서 비롯되는데, Qwen3.5는 Gated Delta Network와 GQA 하이브리드 구조로 KV캐시 증가를 1~2GB로 억제하는 반면, Gemma4는 풀 dense 구조로 256k 컨텍스트에서 40GB까지 VRAM이 상승한다.

**핵심 포인트:** 핵심 차별점: Qwen3.5 27B는 Gemma4 31B보다 적은 파라미터(27B vs 31B)와 VRAM으로 높은 벤치마크 스코어를 달성하며, 효율적인 구조 설계를 통해 중국 오픈소스 LLM의 빠른 기술 발전 추세를 보여준다.

🔗 [threads.com/@cheoeum.ai/post/DW3KePJEQ7I?…](https://www.threads.com/@cheoeum.ai/post/DW3KePJEQ7I?xmt=AQF0cS7mR2vpMNCWoFwv6q6QbhaHBfD7IYjSzAM9LK-RvjE5dO3buVtOK22dSUbq3Uj_tMM&amp;slof=1)

*기타 (Others)*


## AI & RESEARCH

### Amazon Bedrock: 의미론적 검색 기반 생성형 AI 에이전트 구축

<div class="badges"><img src="../assets/badges/claude-pick.png" class="badge" alt="Claude's Pick"> <img src="../assets/badges/s7c-pick.png" class="badge" alt="S7C Pick"></div>

![Amazon Bedrock: 의미론적 검색 기반 생성형 AI 에이전트 구축](images/00.jpg)

기업 검색 시스템에서 키워드 검색만으로는 사용자 의도를 정확히 파악하기 어려운 문제가 있다. Amazon Bedrock, AgentCore, Strands Agents와 Amazon OpenSearch를 결합하여 의미론적 검색과 텍스트 기반 검색을 동시에 활용하는 생성형 AI 에이전트 보조자를 구현함으로써 이를 해결한다. 이 접근법은 자연어 쿼리에 대한 더욱 정확하고 맥락을 고려한 응답을 제공하여 사용자 경험을 개선한다.

**핵심 포인트:** 핵심 기여: Amazon OpenSearch의 하이브리드 검색 기능과 다중 LLM 모델 조율을 통해 의미론적 이해와 정확한 매칭을 동시에 달성하는 멀티모달 검색 에이전트 구현.

🔗 [aws.amazon.com/blogs/machine-learning/bui…](https://aws.amazon.com/blogs/machine-learning/building-intelligent-search-with-amazon-bedrock-and-amazon-opensearch-for-hybrid-rag-solutions/)

*기타 (Others)*

### Mythos Preview — Anthropic의 초강력 AI, 27년 숨은 제로데이 발견

<!-- badge:5 -->
![Mythos Preview — Anthropic의 초강력 AI, 27년 숨은 제로데이 발견](images/06.jpg)

Anthropic이 개발한 Mythos Preview는 기존 AI 모델 대비 사이버보안 능력이 월등히 뛰어나 OpenBSD에서 27년간 숨겨진 취약점을 포함해 수천 개의 제로데이를 발견했다. 이 모델은 단순히 취약점을 찾는 것을 넘어 복잡한 보안망을 연쇄적으로 뚫고 시스템 최고 권한을 탈취하는 익스플로잇 코드를 자동 생성하는 능력을 갖추고 있다. Anthropic은 악용 위험을 차단하기 위해 공개를 보류하고 Project Glasswing을 통해 핵심 방어자들과만 협력하며, 기업들은 기존 AI 모델로 방어 체계를 점검하고 보안 패치 주기를 대폭 단축할 필요가 있다.

**핵심 포인트:** 핵심 성과: SWE-bench Verified 점수 93.9%로 Claude Opus 4.6의 80.8%를 크게 상회하며, 인간 보안 전문가 수준의 제로데이 발견 및 익스플로잇 개발 능력을 달성했다.

🔗 [anthropic.com/glasswing](https://www.anthropic.com/glasswing)

*기타 (Others)*

### AttentionPack

<div class="badges"><img src="../assets/badges/editors-pick.png" class="badge" alt="Editor's Pick"></div>

VLM(시각언어모델) 돌릴 때 램 부족해서 뻗는 일, 이제 확 줄어들 것 같습니다. 성능 저하 없이 KV 캐시 메모리를 328MB에서 15MB로 무려 21배나 줄여버린 재밌는 연구가 나왔네요.

🔗 [arxiv.org/pdf/2603.23914](https://arxiv.org/pdf/2603.23914)

*논문 (Papers)*

### Claude Code — 모델보다 하네스 설계가 AI 성능을 결정

<!-- badge:7 -->
![Claude Code — 모델보다 하네스 설계가 AI 성능을 결정](images/24.jpg)

앤트로픽의 공식 코딩 도구 Claude Code가 동일한 Opus 4.6 모델을 사용하는 38개 서드파티 도구에 벤치마크에서 밀리는 문제가 발생했다. 이는 AI의 실질적 성능이 기반 모델 자체보다 그것을 감싸는 하네스 설계, 즉 시스템 프롬프트와 제어 구조에 더 큰 영향을 받음을 시사한다. 동일한 엔진이라도 이를 어떻게 조련하고 시스템화하는지에 따라 성능 격차가 극명하게 나타나며, 향후 경쟁은 모델 자체가 아닌 실무 환경 맞춤형 최적화에서 비롯될 것으로 분석된다.

**핵심 포인트:** 핵심 통찰: 같은 Opus 4.6 모델 기준 38개 서드파티 도구가 공식 도구를 상회하며, AI 성능의 진정한 경쟁 요소는 시스템 프롬프트와 제어 구조 설계로 이동했음을 입증했다.

🔗 [tbench.ai/leaderboard/terminal-bench/2.0?…](https://www.tbench.ai/leaderboard/terminal-bench/2.0?models=Claude+Opus+4.6)

*기타 (Others)*

### PaperOrchestra: 다중 에이전트 기반 학술논문 자동 생성 시스템

<!-- badge:8 -->
기존 자동화 연구 프레임워크는 실험 실행은 가능하지만 논문 작성 모듈이 가장 약한 부분으로, 문헌 검토는 얕고 인용은 부족하며 개념 다이어그램 생성이 불가능한 한계가 있다. PaperOrchestra는 전문화된 에이전트들을 활용해 원본 아이디어, 실험 로그, 노트를 투고 가능한 LaTeX 원고로 변환하는 다중 에이전트 시스템으로, 깊은 문헌 종합, 플롯 생성, 개념 다이어그램 작성, 반복 개선을 담당한다. 인간 평가에서 문헌 검토 품질 50~68%, 전체 원고 품질 14~38% 향상을 달성했다.

**핵심 포인트:** 핵심 성과: 인간 평가 결과 기존 자동화 기준선 대비 문헌 검토 품질에서 50~68% 절대 우위, 전체 원고 품질에서 14~38% 우위 달성. 또한 200개 상위급 AI 학술지 논문을 역공학으로 구성한 PaperWritingBench 벤치마크 최초 공개.

🔗 [linkedin.com/posts/new-paper-from-google…](https://www.linkedin.com/posts/new-paper-from-google-on-multi-agent-research-share-7447662811314278400-EF2e?utm_source=social_share_send&amp;utm_medium=ios_app&amp;rcm=ACoAAER21kcBd_iBPigZtQJrxT6dDwTFPgWD12k&amp;utm_campaign=share_via)

*기타 (Others)*


## DEVTOOLS & OPEN SOURCE

### LMCache — RAG·긴 컨텍스트 LLM 첫 응답 지연시간 최대 10배 단축

<!-- badge:9 -->
![LMCache — RAG·긴 컨텍스트 LLM 첫 응답 지연시간 최대 10배 단축](images/04.jpg)

RAG나 긴 컨텍스트를 처리하는 LLM 서빙 시 첫 응답 시간(TTFT)이 느린 문제를 해결하는 KV 캐시 최적화 도구. 중복되는 텍스트의 KV 캐시를 GPU, CPU 메모리, 로컬 디스크에 저장했다가 재사용함으로써 반복 계산을 제거한다. vLLM과 함께 사용할 경우 멀티턴 QA와 RAG 환경에서 3~10배의 지연시간 단축을 달성하며, pip install로 간단히 설치 가능하다.

**핵심 포인트:** 핵심 성과: vLLM 결합 시 RAG 및 멀티턴 QA에서 지연시간 3~10배 단축, GPU 연산 비용 절감과 함께 사용자 응답 속도 대폭 개선

🔗 [github.com/LMCache/LMCache](https://github.com/LMCache/LMCache)

*GitHub*

### Graphify — LLM 기반 지식 그래프로 대규모 코드베이스 71배 효율적 탐색

<div class="badges"><img src="../assets/badges/editors-pick.png" class="badge" alt="Editor's Pick"></div>

LLM에게 전체 코드베이스를 컨텍스트에 넣으면 토큰 폭증과 정확도 하락 문제가 발생한다. Graphify는 폴더 지정 후 한 줄 명령으로 자동 지식 그래프를 생성하고, 필요한 노드만 선택적으로 읽어 쿼리당 토큰 사용량을 71.5배 절감한다. 13개 프로그래밍 언어와 PDF, 이미지를 지원하며, 자연어 Q&A를 통해 코드 의존성, 함수 호출 관계, 프로젝트 아키텍처를 즉시 파악할 수 있다.

**핵심 포인트:** 핵심 성과: 쿼리당 토큰 사용량 71.5배 절감으로 LLM 에이전트의 대규모 코드베이스 이해 효율성을 획기적으로 향상. 사람의 인지 방식과 동일한 구조화된 그래프 기반 접근으로 정확도와 비용 효율성을 동시에 실현.

🔗 [linkedin.com/posts/seungpil_github-safish…](https://www.linkedin.com/posts/seungpil_github-safishamsigraphify-ai-coding-assistant-activity-7447433046280118273-gm7-?utm_medium=ios_app&amp;rcm=ACoAAER21kcBd_iBPigZtQJrxT6dDwTFPgWD12k&amp;utm_source=social_share_send&amp;utm_campaign=share_via)

*기타 (Others)*

### MemPalace — 할리우드 배우가 공개한 오픈소스 AI 메모리 시스템

<!-- badge:11 -->
![MemPalace — 할리우드 배우가 공개한 오픈소스 AI 메모리 시스템](images/07.jpg)

AI 에이전트가 과거 대화와 기록을 효과적으로 관리하지 못하는 문제를 해결하기 위해 개발된 오픈소스 메모리 시스템. MemPalace는 로컬 환경에서 구동되는 최고 성능의 메모리 관리 솔루션으로, LongMemEval 벤치마크에서 96.6%의 높은 성능을 기록했다. MCP를 통해 통합 가능하며 과거 기록의 검색과 조회를 자동화할 수 있어 개발자가 커스터마이징하여 활용할 수 있다.

**핵심 포인트:** 핵심 성과: LongMemEval 벤치마크 96.6% 달성, 무료 오픈소스 공개, 로컬 메모리 시스템으로 과거 기록 자동 검색 및 조회 기능 제공

🔗 [github.com/milla-jovovich/mempalace](https://github.com/milla-jovovich/mempalace)

*GitHub*

### Agent Skills — AI 코딩 에이전트를 위한 프로덕션급 엔지니어링 스킬셋

<div class="badges"><img src="../assets/badges/s7c-pick.png" class="badge" alt="S7C Pick"></div>

![Agent Skills — AI 코딩 에이전트를 위한 프로덕션급 엔지니어링 스킬셋](images/08.jpg)

AI 코딩 에이전트는 테스트와 보안 검토를 생략하고 빠르게 작동하는 코드만 생성하려는 경향이 있다. Agent Skills는 구글 크롬 팀의 Addy Osmani가 공개한 오픈소스 스킬셋으로, 6개의 간단한 명령어를 통해 설계, 테스트, 코드 리뷰, 배포까지 구글의 시니어 엔지니어링 작업 방식을 AI 에이전트에게 강제하여 프로덕션 수준의 코드 품질을 보장한다.

**핵심 포인트:** 핵심 기여: 6개의 명령어만으로 설계부터 배포까지 전체 엔지니어링 워크플로우를 AI 에이전트에게 강제하여, 테스트 생략과 보안 검토 회피를 원천 차단하는 구글의 시니어 엔지니어링 방식을 재현한다.

🔗 [github.com/addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)

*GitHub*

### TurboQuant — 정확도 손실 없이 LLM 추론 속도 최적화

<div class="badges"><img src="../assets/badges/editors-pick.png" class="badge" alt="Editor's Pick"></div>

![TurboQuant — 정확도 손실 없이 LLM 추론 속도 최적화](images/09.jpg)

LLM 추론 시 정확도를 유지하면서 속도를 높이기 위해 기존에는 정확도를 타협해야 했던 문제가 있었다. 구글의 TurboQuant는 제로 정확도 손실 기준으로 모델 사이즈를 압축하는 양자화 기술을 제공한다. 특히 메모리 사용량의 주요 원인인 KV 캐시 압축과 벡터 검색에 최적화되어 있으며, CUDA 12, 13 기반의 cuTile과 PyTorch를 지원하여 실무 적용이 용이하다.

**핵심 포인트:** 핵심 성과: 정확도 손실 없이 모델 사이즈 압축 및 KV 캐시 메모리 최적화를 동시에 달성하며, pip install turboquant-gpu로 간단히 설치되어 LLM 서빙 및 추론 최적화 작업에 즉시 적용 가능하다.

🔗 [github.com/DevTechJr/turboquant-gpu](https://github.com/DevTechJr/turboquant-gpu)

*GitHub*

### career-ops

<!-- badge:14 -->
![career-ops](images/13.jpg)

와... AI기반 취업 도구를 무료로 풀었습니다 구직 활동은 외롭고도 지치는 싸움입니다. 수많은 공고를 뒤지고, 기업마다 이력서를 고치고, 결과를 기다리는 과정은 끝이 보이지 않죠.

🔗 [github.com/santifer/career-ops](https://github.com/santifer/career-ops)

*GitHub*

### loopndroll

<!-- badge:15 -->
![loopndroll](images/14.jpg)

한 개발자(Alex Barashkov)가 최신 Codex의 'Hooks' 기능을 활용해 에이전트가 절대 쉬지 않고 일하게 만드는 macOS 전용 툴바 앱 'Loopndroll'을 오픈소스로 공개했습니다.

🔗 [github.com/lnikell/loopndroll](https://github.com/lnikell/loopndroll)

*GitHub*

### ULTRAPLAN — Claude의 30분 클라우드 계획 기능 정식 출시

<div class="badges"><img src="../assets/badges/editors-pick.png" class="badge" alt="Editor's Pick"> <img src="../assets/badges/s7c-pick.png" class="badge" alt="S7C Pick"></div>

![ULTRAPLAN — Claude의 30분 클라우드 계획 기능 정식 출시](images/15.jpg)

대규모 코드 작업을 계획할 때 개발자가 터미널에서 기다려야 하는 문제를 해결하기 위해 Anthropic이 ULTRAPLAN을 출시했다. 터미널에서 명령어로 시작하면 Claude Code on the Web 세션에서 클라우드 기반으로 계획을 생성하는 동안 개발자는 다른 작업을 수행할 수 있다. 생성된 계획을 브라우저에서 인라인 코멘트, 이모지 반응, 섹션 네비게이션으로 검토하고, 클라우드에서 직접 구현하거나 로컬 터미널로 돌려받아 실행할 수 있다.

**핵심 포인트:** 핵심 기여: 비동기식 계획 생성으로 터미널 블로킹 시간을 제거하고, 브라우저 기반 협업형 검토 인터페이스 제공하며, 클라우드 직접 실행 또는 로컬 실행의 두 가지 실행 경로 지원.

🔗 [code.claude.com/docs/en/ultraplan](https://code.claude.com/docs/en/ultraplan)

*기타 (Others)*

### demos

<!-- badge:17 -->
![demos](images/16.jpg)

올해 본 아이디어중 손에 꼽을 정도로 놀랍습니다. 엔조 마누엘 망가노(Enzo Manuel Mangano)가 React Native WebGPU를 활용해 만든 오픈소스 애니메이션 데모입니다.

🔗 [github.com/enzomanuelmangano/demos](https://github.com/enzomanuelmangano/demos)

*GitHub*

### 442a6bf555914893e9891c11519de94f

<!-- badge:18 -->
![442a6bf555914893e9891c11519de94f](images/19.jpg)

안드레 카파시가 제안한 'LLM 위키' 개념이 하루 만에 270만 회를 넘길 정도로 전 세계 개발자들 사이에서 폭발적인 반응을 얻고 있습니다. 안드레 카파시는 LLM을 활용한 ‘LLM 위키’ 구축 아이디어를 구체화한 Gist 문서까지 공개를 했는데요.

🔗 [gist.github.com/karpathy/442a6bf555914893…](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

*GitHub*

### timesfm

<!-- badge:19 -->
![timesfm](images/25.jpg)

구글 리서치의 TimesFM, 지금 GitHub 트렌딩 3위입니다. 시계열 예측을 위한 파운데이션 모델로, 별도 학습 없이 사전 훈련된 모델로 바로 예측이 가능합니다. JAX와 PyTorch 모두 지원하고, Apple Silicon 포함 다양한 환경에서 동작합니다.

🔗 [github.com/google-research/timesfm](https://github.com/google-research/timesfm)

*GitHub*

### system_prompts_leaks

<!-- badge:20 -->
![system_prompts_leaks](images/28.jpg)

AI 회사들이 절대 공개 안 하는 걸 누군가 계속 모아두고 있다 AI 회사들이 공개 안 하는 시스템 프롬프트. GPT-5.4, Claude Opus 4.6, Gemini 3.1 Pro, Grok 4.2… 주요

🔗 [github.com/asgeirtj/system_prompts_leaks](http://github.com/asgeirtj/system_prompts_leaks)

*GitHub*


## ENGINEERING

### AI 에이전트가 진화하려면 모델 가중치만 업데이트하면 될까요?

<!-- badge:21 -->
![AI 에이전트가 진화하려면 모델 가중치만 업데이트하면 될까요?](images/11.jpg)

AI 에이전트가 진화하려면 모델 가중치만 업데이트하면 될까요? 랭체인에서 에이전트의 지속 학습(Continual Learning)을 3가지 레이어로 심플하게 정리했습니다.

🔗 [blog.langchain.com/continual-learning-for…](https://blog.langchain.com/continual-learning-for-ai-agents/)

*블로그 (Blog)*


## PRODUCT & INDUSTRY

### Gemini Notebooks — 제미나이와 NotebookLM 연동 프로젝트 관리

<!-- badge:22 -->
![Gemini Notebooks — 제미나이와 NotebookLM 연동 프로젝트 관리](images/01.jpg)

사용자들이 제미나이에서 대화 기록, PDF, 파일 등을 프로젝트 단위로 관리하기 어려운 문제를 해결하기 위해 구글이 제미나이 앱에 노트북 기능을 출시했다. 이 기능은 구글의 AI 리서치 도구인 NotebookLM과 완벽하게 동기화되어, 사용자가 제미나이에서 수집한 자료와 대화 맥락을 그대로 NotebookLM으로 전달하여 시각화 자료나 팟캐스트를 생성할 수 있게 한다.

**핵심 포인트:** 핵심 기여: 제미나이와 NotebookLM 간 완벽한 동기화를 통해 자료 수집부터 시각화 및 팟캐스트 생성까지 일관된 워크플로우를 제공하며, 프로젝트 단위의 통합 관리 공간을 구현했다.

🔗 [blog.google/innovation-and-ai/products/ge…](https://blog.google/innovation-and-ai/products/gemini-app/notebooks-gemini-notebooklm/)

*블로그 (Blog)*

### Chrome — 수직 탭 기능과 몰입형 읽기 모드 공식 도입

<!-- badge:23 -->
![Chrome — 수직 탭 기능과 몰입형 읽기 모드 공식 도입](images/02.jpg)

Chrome 브라우저의 탭 관리 문제를 해결하기 위해 Google이 수직 탭 기능과 몰입형 읽기 모드를 공식 도입했다. 수직 탭 기능은 탭을 화면 왼쪽에 세로로 배치하여 많은 수의 탭을 열어도 제목이 잘리지 않고 한눈에 파악할 수 있도록 한다. 몰입형 읽기 모드는 시각적 방해 요소를 제거하여 사용자가 콘텐츠에 집중할 수 있는 환경을 제공한다.

**핵심 포인트:** 핵심 기여: 수직 탭 배치로 탭 오버플로우 문제 해결 및 시각적 간결성 확보, 몰입형 읽기 모드로 방해 요소 제거하여 콘텐츠 집중도 향상

🔗 [threads.com/@choi.openai/post/DW3WlS_DXKW…](https://www.threads.com/@choi.openai/post/DW3WlS_DXKW?xmt=AQF0QQbiz0mGkqLEbSPCchzq91efToL0ik8RsSE2LSKYF1IQncRGGATUv8cYxIuCfj_2I6yr&amp;slof=1)

*기타 (Others)*

### 스레드에 업로드 했던 내용을 문서로 정리해 에이전트가 바로 읽을 수 있는 개인 위키를 구현...

<!-- badge:24 -->
![스레드에 업로드 했던 내용을 문서로 정리해 에이전트가 바로 읽을 수 있는 개인 위키를 구현...](images/12.jpg)

스레드에 업로드 했던 내용을 문서로 정리해 에이전트가 바로 읽을 수 있는 개인 위키를 구현했습니다. 구조적인 글을 쓰고 인용을 해야하는 일들이 많다보니, RAG보다 파일 구조와 백링크 기반 탐색이 더 안정적이었는데요.

🔗 [threads.com/@choi.openai/post/DWyQUYvAQyH…](https://www.threads.com/@choi.openai/post/DWyQUYvAQyH?xmt=AQF08YDnzY61om_cpYZqHxeyttv9J4mEkPa6bvBOjkTEh9iH93kpScGuNNF72CshJkPgeZQ&amp;slof=1)

*기타 (Others)*

### kordoc-ai 프로토타입에서 제일 킬러 피처(killer-feature)라고 생각하는거

<!-- badge:25 -->
![kordoc-ai 프로토타입에서 제일 킬러 피처(killer-feature)라고 생각하는거](images/18.jpg)

kordoc-ai 프로토타입에서 제일 킬러 피처(killer-feature)라고 생각하는거

🔗 [threads.com/@chris_gomdori/post/DWutGG5k7…](https://www.threads.com/@chris_gomdori/post/DWutGG5k7GK?xmt=AQF0gkIlZP570Zil2UmXkbCEEsDHRjZ8GFVBQpNZEIDQ3jnGNlWCfuhZWVI43s49JW7B77Cs&amp;slof=1)

*기타 (Others)*

### :space

<!-- badge:26 -->
:space

🔗 [linkedin.com/posts/claude-code-langsmith…](https://www.linkedin.com/posts/claude-code-langsmith-weve-shipped-share-7445903647319744512-xBxk?utm_source=social_share_send&amp;utm_medium=ios_app&amp;rcm=ACoAAER21kcBd_iBPigZtQJrxT6dDwTFPgWD12k&amp;utm_campaign=share_via)

*기타 (Others)*

### CLAUDE

<!-- badge:27 -->
지침, 스킬, 에이전트, 훅, 커넥터... 이거 다 터미널에서 하나하나 확인하고 있었거든요? 이제 대시보드 하나로 다 봅니다.

🔗 [note.md/](http://note.md/)

*기타 (Others)*

### 구글이 결국 판을 바꿨습니다.

<!-- badge:28 -->
![구글이 결국 판을 바꿨습니다.](images/23.jpg)

구글이 결국 판을 바꿨습니다. 오픈 모델 "Gemma 4"가 Apache 2.0으로 공개되면서, 이제 기업들도 데이터 외부 유출 걱정 없이 자체 AI를 직접 구축할 수 있게 됐습니다. 로컬 실행, 에이전트 기능까지 가능한 핵심 사례를 모았습니다:thread:

🔗 [blog.google/innovation-and-ai/technology…](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4)

*기타 (Others)*

### Anthropic

<div class="badges"><img src="../assets/badges/editors-pick.png" class="badge" alt="Editor's Pick"></div>

Anthropic이 당신 코드에는 "AI가 공동 저작했습니다"를 자동으로 붙이고 자기 직원 코드에서는 AI 흔적을 지우고 있었음. 이번 주 유출된 소스코드에서 두 기능이 동시에 발견됨.

🔗 [axios.com/2026/03/31/anthropic-leaked-sou…](https://www.axios.com/2026/03/31/anthropic-leaked-source-code-ai)

*기타 (Others)*

### SSE

<!-- badge:30 -->
![SSE](images/27.jpg)

Claude Code 2.1.90 /powerup으로 Claude Code 기능을 인터랙티브 데모와 함께 배울 수 있게 되었습니다. SSE·SDK 핵심 경로의 O(n²) 성능 병목도 모두 해결되었습니다.

🔗 [threads.com/@ok_min87/post/DWnL5r6E69G?xm…](https://www.threads.com/@ok_min87/post/DWnL5r6E69G?xmt=AQF0xuGi8H08NdoPFjZQaP5lAhClpU8k4LNFR5b_RuIHDMMyVAuTZxPfQIi9nAxZDdlCbjrr&amp;slof=1)

*기타 (Others)*

### (제목 없음)

<!-- badge:31 -->
![(제목 없음)](images/30.jpg)

🔗 [blog.langchain.com/langgraph-platform-ann…](https://blog.langchain.com/langgraph-platform-announce/)

*기타 (Others)*

### (제목 없음)

<!-- badge:32 -->
![(제목 없음)](images/31.jpg)

🔗 [claude.com/blog/claude-managed-agents](https://claude.com/blog/claude-managed-agents)

*기타 (Others)*


