# Computer Vision 과제 환경 설정 가이드

## 개요
이 문서는 Computer Vision 코스의 모든 Programming Assignment (PA1, PA2, PA3 등)를 수행하기 위한 **통합 환경 설정** 가이드입니다.

`uv`를 사용하여 `computer_vision` 프로젝트 레벨에서 하나의 가상환경과 패키지를 관리합니다.

### 왜 통합 환경인가?
- ✅ **효율성**: 같은 패키지(numpy, opencv 등)를 여러 번 설치하지 않음
- ✅ **디스크 절약**: 하나의 `.venv`만 생성 (~300MB), 개별 환경 대비 N배 절약
- ✅ **관리 편의성**: 한 번만 activate하면 모든 PA에서 사용
- ✅ **코드 재사용**: 과제 간 유틸리티 함수 공유 가능
- ✅ **버전 일관성**: 모든 과제에서 동일한 패키지 버전 사용

## 1. UV 설치

UV는 Rust로 작성된 빠르고 현대적인 Python 패키지 및 프로젝트 매니저입니다.

### macOS/Linux 설치
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 설치 확인
```bash
uv --version
```

정상적으로 설치되었다면 버전 정보가 출력됩니다 (예: `uv 0.x.x`).

## 2. 프로젝트 디렉토리 구조

```
computer_vision/                 # 프로젝트 루트
├── .venv/                       # ⭐ 통합 가상환경 (모든 PA 공유)
├── .gitignore                   # .venv 제외
├── pyproject.toml               # (선택) 프로젝트 설정
├── requirements.txt             # (선택) 전체 의존성
│
├── PA1/                         # Programming Assignment 1
│   ├── Computer Vision PA1.pdf
│   ├── docs/
│   │   ├── PA1_prepare.md      # 이 파일
│   │   └── PA1_solution.md
│   ├── images/                  # 스테레오 이미지 쌍
│   │   ├── reindeer_left.png
│   │   ├── reindeer_right.png
│   │   └── ...
│   ├── output/                  # 결과 저장 (생성 필요)
│   ├── practice/
│   ├── stereo_matching.py      # 메인 구현 파일
│   └── visualize_disparity_3d.py
│
├── PA2/                         # Programming Assignment 2
│   └── (향후 추가)
│
└── PA3/                         # Programming Assignment 3
    └── (향후 추가)
```

**핵심 포인트:**
- `.venv`는 `computer_vision/` 레벨에 **단 1개**만 생성
- 모든 PA (PA1, PA2, PA3 등)가 이 환경을 공유
- 각 PA는 독립적인 디렉토리 유지

## 3. 가상환경 생성 및 활성화

### 3.1 프로젝트 루트로 이동
```bash
cd /Users/wesley/Desktop/wooshikwon/computer_vision
```

**중요**: PA1이 아닌 `computer_vision` 디렉토리에서 작업합니다.

### 3.2 UV로 가상환경 생성
```bash
uv venv
```

이 명령어는 `computer_vision/.venv` 디렉토리에 가상환경을 생성합니다.

**한 번만 실행하면 됩니다!** 모든 PA (PA1, PA2, PA3 등)가 이 환경을 공유합니다.

### 3.3 가상환경 활성화

**macOS/Linux:**
```bash
source .venv/bin/activate
```

활성화되면 터미널 프롬프트에 `(.venv)`가 표시됩니다.

### 3.4 모든 PA에서 사용
```bash
# 한 번 activate하면
cd PA1 && python stereo_matching.py      # PA1 작업
cd ../PA2 && python feature_detect.py    # PA2 작업 (환경 그대로)
cd ../PA3 && python object_detect.py     # PA3 작업 (환경 그대로)
```

환경을 여러 번 전환할 필요가 없습니다!

## 4. 필수 패키지 설치

### 4.1 기본 패키지 설치 (PA1 기준)

PA1을 포함한 대부분의 Computer Vision 과제에 필요한 패키지들을 설치합니다.

```bash
# computer_vision 디렉토리에서 가상환경 활성화 후
uv pip install numpy opencv-python matplotlib scipy scikit-image
```

**패키지 설명:**
- `numpy`: 수치 연산 및 배열 처리
- `opencv-python`: 컴퓨터 비전 라이브러리 (이미지 입출력, 필터링)
- `matplotlib`: 2D/3D 시각화
- `scipy`: 과학 계산 (선택, 고급 필터링에 유용)
- `scikit-image`: 이미지 처리 유틸리티 (선택)

**최소 설치 (PA1만):**
```bash
uv pip install numpy opencv-python matplotlib
```

### 4.2 설치 확인
```bash
python -c "import numpy; import cv2; import matplotlib; print('All packages installed successfully')"
```

오류 없이 "All packages installed successfully"가 출력되면 정상입니다.

### 4.3 향후 PA2, PA3에 추가 패키지 필요 시
```bash
# 같은 환경에 추가 설치
cd /Users/wesley/Desktop/wooshikwon/computer_vision
source .venv/bin/activate

# 예: PA2에서 scikit-learn 필요 시
uv pip install scikit-learn

# 예: PA3에서 Pillow, Pandas 필요 시
uv pip install pillow pandas
```

**통합 환경의 장점**: 한 번 설치한 패키지는 모든 PA에서 사용 가능!

## 5. PA1 출력 디렉토리 생성

결과 이미지를 저장할 `output` 디렉토리를 PA1에 생성:
```bash
cd PA1
mkdir -p output
```

## 6. 환경 검증

### 6.1 Python 버전 확인
```bash
python --version
```

Python 3.8 이상이 권장됩니다.

### 6.2 패키지 버전 확인
```bash
uv pip list
```

다음과 유사한 출력이 나와야 합니다:
```
numpy           1.24.x
opencv-python   4.8.x
matplotlib      3.7.x
scipy           1.11.x
scikit-image    0.21.x
```

### 6.3 PA1 테스트 실행
```bash
# computer_vision 디렉토리에서
cd PA1
python stereo_matching.py
```

TODO 부분을 구현하지 않았다면 오류가 발생할 수 있지만, **import 오류가 없다면 환경은 정상**입니다.

## 7. 개발 도구 설정 (선택사항)

### 7.1 VS Code 사용 시
1. Python 확장 설치 (Microsoft)
2. `Cmd+Shift+P` → "Python: Select Interpreter"
3. `computer_vision/.venv/bin/python` 선택 ⭐
4. 모든 PA 파일에서 자동으로 이 인터프리터 사용

### 7.2 IPython 설치 (대화형 개발에 유용)
```bash
uv pip install ipython
```

### 7.3 Jupyter Notebook (선택)
```bash
uv pip install jupyter
jupyter notebook
```

## 8. 가상환경 비활성화

작업 완료 후 가상환경을 비활성화:
```bash
deactivate
```

## 9. 다음 단계

환경 설정이 완료되었다면 `PA1_solution.md`를 참고하여 과제를 진행하세요.

주요 구현 파일:
- `stereo_matching.py`: TODO1~TODO7 구현
- `visualize_disparity_3d.py`: 3D 시각화 (필요시 경로 수정)

## 10. 문제 해결

### "command not found: uv"
- UV 설치 후 터미널을 재시작하거나 `source ~/.bashrc` (또는 `~/.zshrc`) 실행

### "No module named 'cv2'"
- `uv pip install opencv-python` 다시 실행
- 가상환경이 활성화되었는지 확인

### UV가 느리거나 문제가 있는 경우
UV는 일반적으로 pip보다 훨씬 빠르지만, 문제 발생 시 다음으로 대체 가능:
```bash
python -m pip install numpy opencv-python matplotlib
```

## 11. 프로젝트 관리

### 11.1 전체 프로젝트 requirements 생성
```bash
cd /Users/wesley/Desktop/wooshikwon/computer_vision
source .venv/bin/activate
uv pip freeze > requirements.txt
```

이 파일은 모든 PA에서 사용하는 패키지 목록을 포함합니다.

### 11.2 과제별 requirements 추출 (제출 시)

PA1만의 의존성을 명시하고 싶다면:

```bash
# PA1/requirements.txt 수동 작성
cat > PA1/requirements.txt << EOF
numpy>=1.24.0
opencv-python>=4.8.0
matplotlib>=3.7.0
EOF
```

또는 전체 환경을 복사:
```bash
cd computer_vision
uv pip freeze > PA1/requirements.txt
```

### 11.3 pyproject.toml 활용 (고급)

프로젝트 전체를 체계적으로 관리하려면:

```bash
cd /Users/wesley/Desktop/wooshikwon/computer_vision
cat > pyproject.toml << EOF
[project]
name = "computer-vision-course"
version = "0.1.0"
description = "GCB6104/GEK6225 Computer Vision Programming Assignments"
requires-python = ">=3.8"
dependencies = [
    "numpy>=1.24.0",
    "opencv-python>=4.8.0",
    "matplotlib>=3.7.0",
    "scipy>=1.11.0",
    "scikit-image>=0.21.0",
]

[tool.uv]
dev-dependencies = [
    "ipython",
    "jupyter",
]
EOF
```

설치:
```bash
uv pip install -e .
```

### 11.4 다른 환경에서 복원
```bash
# 새로운 컴퓨터나 팀원과 공유 시
git clone <your-repo>
cd computer_vision
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
# 또는
uv pip install -e .
```

## 12. UV의 장점

- **속도**: pip 대비 10-100배 빠른 패키지 설치
- **정확성**: 더 정확한 의존성 해결
- **현대적**: pyproject.toml 기반 프로젝트 관리
- **단순함**: conda 없이 Python 버전 및 환경 관리 가능
- **일관성**: lockfile 지원으로 정확한 재현 가능

## 13. 통합 환경 vs 개별 환경

### 언제 개별 환경이 필요한가?

다음 경우에만 PA별로 개별 환경 고려:
- PA2가 TensorFlow 2.10 필요, PA3가 PyTorch 1.13 필요 (버전 충돌)
- 특정 PA가 Python 버전이 다름 (예: PA1은 3.10, PA2는 3.8)
- 과제를 완전히 격리해야 하는 특수한 경우

**현재 상황**: 모든 PA가 컴퓨터 비전 과제이므로 **통합 환경이 최적**입니다.

## 14. 빠른 시작 요약

```bash
# 1. UV 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 환경 생성 및 활성화
cd /Users/wesley/Desktop/wooshikwon/computer_vision
uv venv
source .venv/bin/activate

# 3. 패키지 설치
uv pip install numpy opencv-python matplotlib scipy scikit-image

# 4. PA1 실행
cd PA1
mkdir -p output
python stereo_matching.py

# 5. 향후 PA2, PA3에서도 같은 환경 사용
cd ../PA2
python your_script.py  # 환경 그대로 사용
```

---

**준비 완료!** 이제 모든 PA를 효율적으로 수행할 수 있습니다.

궁금한 점이 있으면 `PA1/docs/PA1_solution.md`를 참고하세요.
