# PA1 완전 솔루션 가이드

## 목차
1. [스테레오 매칭 개요](#1-스테레오-매칭-개요)
2. [전체 파이프라인 흐름](#2-전체-파이프라인-흐름)
3. [TODO1: 이미지 시프팅](#3-todo1-이미지-시프팅)
4. [TODO2: SAD 계산 (Cost Volume 구축)](#4-todo2-sad-계산-cost-volume-구축)
5. [TODO3: Cost Aggregation (Box Filter)](#5-todo3-cost-aggregation-box-filter)
6. [TODO4: Disparity Selection (Winner-Takes-All)](#6-todo4-disparity-selection-winner-takes-all)
7. [기본 구현 검증](#7-기본-구현-검증)
8. [TODO6: Joint Bilateral Filter (고급)](#8-todo6-joint-bilateral-filter-고급)
9. [TODO7: Weighted Median Filter (고급)](#9-todo7-weighted-median-filter-고급)
10. [최종 코드 및 결과](#10-최종-코드-및-결과)

---

## 1. 스테레오 매칭 개요

### 1.1 스테레오 비전의 원리

스테레오 비전은 두 개의 카메라(왼쪽, 오른쪽)로 촬영한 이미지 쌍으로부터 깊이(depth) 정보를 추정하는 기술입니다.

**핵심 개념:**
- **Disparity (시차)**: 동일한 3D 점이 왼쪽과 오른쪽 이미지에서 나타나는 위치 차이
- **깊이와 시차의 관계**: `depth = (baseline × focal_length) / disparity`
- 시차가 클수록 → 물체가 가까움
- 시차가 작을수록 → 물체가 멀리 있음

### 1.2 스테레오 매칭 문제

**목표**: 왼쪽 이미지의 각 픽셀 (x, y)에 대해, 오른쪽 이미지에서 대응되는 픽셀을 찾아 disparity를 계산

**가정 (Rectified Stereo):**
- 두 이미지가 정렬되어 있어 대응점이 같은 y 좌표(수평선)에 존재
- 따라서 x 방향으로만 탐색하면 됨

**수식:**
```
왼쪽 이미지 픽셀 (x, y) ↔ 오른쪽 이미지 픽셀 (x - d, y)
여기서 d는 disparity (0 ≤ d < max_disparity)
```

---

## 2. 전체 파이프라인 흐름

PA1의 스테레오 매칭 파이프라인은 다음과 같이 구성됩니다:

```
[1] 이미지 로딩
    ↓
[2] Cost Volume 구축 ────────┐
    │                        │
    ├─ TODO1: Image Shifting │ ← 각 disparity d에 대해
    └─ TODO2: SAD 계산       │   오른쪽 이미지를 d만큼 이동 후
                             │   픽셀 차이의 절댓값 계산
                             ↓
[3] Cost Aggregation ─────────┐
    │                         │
    └─ TODO3: Box Filter      │ ← 주변 픽셀의 cost를 합산하여
                              │   노이즈 감소 및 신뢰도 향상
                              ↓
[4] Disparity Selection ──────┐
    │                         │
    └─ TODO4: Winner-Takes-All│ ← 각 픽셀에서 cost가 최소인
                              │   disparity를 선택
                              ↓
[5] Post-processing (선택) ───┐
    │                         │
    ├─ TODO6: Joint Bilateral │ ← Edge-aware smoothing
    └─ TODO7: Weighted Median │ ← Robust outlier filtering
                              ↓
[6] 결과 시각화 및 저장
```

**각 단계의 입출력:**
- **Input**: Left image (H×W), Right image (H×W)
- **After [2]**: Cost Volume (H×W×D), D=max_disparity
- **After [3]**: Aggregated Cost Volume (H×W×D)
- **After [4]**: Disparity Map (H×W)
- **Output**: Disparity Map (H×W), normalized visualization (H×W, 0-255)

---

## 3. TODO1: 이미지 시프팅

### 3.1 이론적 배경

스테레오 매칭에서 **이미지 시프팅**은 오른쪽 이미지를 왼쪽으로 d 픽셀만큼 이동시켜, 왼쪽 이미지와 픽셀 단위로 비교 가능하게 만드는 작업입니다.

**왜 필요한가?**
- 왼쪽 이미지의 픽셀 (x, y)와 오른쪽 이미지의 픽셀 (x-d, y)가 같은 3D 점을 가리킴
- 비교를 쉽게 하기 위해 오른쪽 이미지를 d만큼 shift하면:
  - `shifted_right[x, y] = right[x-d, y]`
  - 이제 `left[x, y]`와 `shifted_right[x, y]`를 직접 비교 가능

**경계 처리:**
- 왼쪽으로 shift하면 오른쪽 끝 d개 픽셀은 유효한 값이 없음 → 0으로 채움
- 실제 cost 계산 시 해당 영역은 invalid로 마킹 (큰 값 할당)

### 3.2 파이프라인 위치

```
build_cost_volume() 내부:
  for d in range(max_disparity):
    → TODO1: r_shift = shift_right_image(right, d)  ← 여기!
    → TODO2: diff = SAD 계산
```

### 3.3 모범 답안

**파일**: `stereo_matching.py`, 함수 `build_cost_volume()` 내부 (line 25)

```python
# TODO1: image shift
r_shift = shift_right_image(right_f, d)
```

**설명:**
- `right_f`는 float32로 변환된 오른쪽 이미지
- `d`는 현재 반복문에서 처리 중인 disparity 값
- `shift_right_image()` 함수는 이미 구현되어 있음 (line 8-14):
  ```python
  def shift_right_image(right, d):
      if d == 0:
          return right
      h, w = right.shape
      shifted = np.zeros_like(right)
      shifted[:, d:] = right[:, :w-d]  # 왼쪽으로 d만큼 이동
      return shifted
  ```
- 반환값: d만큼 왼쪽으로 이동된 이미지 (H×W)

### 3.4 구현 세부사항

**핵심 로직 분석:**
```python
shifted[:, d:] = right[:, :w-d]
```

이 한 줄이 의미하는 것:
- `right[:, :w-d]`: 오른쪽 이미지의 왼쪽부터 (w-d)개 열 선택
- `shifted[:, d:]`: 새 이미지의 d번째 열부터 끝까지
- 결과: 오른쪽 이미지의 내용이 d칸 왼쪽으로 이동
- 왼쪽 d개 열은 0으로 남음 (zeros_like로 초기화)

**시각적 예시 (d=2):**
```
Original right:  [a b c d e f g h]
Shifted (d=2):   [0 0 a b c d e f]
                     ↑
                  왼쪽 2칸은 0으로 채워짐
```

### 3.5 디버깅 팁

- `d=0`일 때: 원본 이미지 그대로 반환 (shift 없음)
- `d > 0`일 때: `shifted.shape == right.shape` 확인
- `shifted[:, :d]`가 모두 0인지 확인
- `shifted[:, d:] == right[:, :w-d]` 확인

---

## 4. TODO2: SAD 계산 (Cost Volume 구축)

### 4.1 이론적 배경

**SAD (Sum of Absolute Differences)**는 스테레오 매칭에서 가장 기본적인 매칭 비용(cost) 측정 방법입니다.

**원리:**
- 두 픽셀의 밝기 차이의 절댓값을 cost로 사용
- 픽셀 값이 유사할수록 → cost 작음 (잘 매칭됨)
- 픽셀 값이 다를수록 → cost 큼 (잘 매칭 안 됨)

**수식:**
```
cost(x, y, d) = |I_left(x, y) - I_right(x - d, y)|
```

**왜 SAD를 사용하는가?**
- **단순성**: 계산이 빠름
- **효과성**: Lambertian surface 가정 하에서 잘 작동
- **대안들**: SSD (제곱차), NCC (normalized correlation), Census transform 등

### 4.2 파이프라인 위치

```
build_cost_volume():
  cost_vol = zeros(H, W, D)
  for d in range(D):
    r_shift = shift_right_image(right, d)
    → TODO2: diff = |left - r_shift|  ← 여기!
    cost_vol[:, :, d] = diff
```

**Cost Volume이란?**
- 3차원 텐서 (H × W × D)
- H, W: 이미지 높이, 너비
- D: 최대 disparity (max_disp)
- `cost_vol[y, x, d]`: 픽셀 (x, y)에서 disparity d일 때의 매칭 비용

### 4.3 모범 답안

**파일**: `stereo_matching.py`, 함수 `build_cost_volume()` 내부 (line 28)

```python
# TODO2: SAD
diff = np.abs(left_f - r_shift)
```

**설명:**
- `left_f`: float32 왼쪽 이미지 (H×W)
- `r_shift`: d만큼 이동된 오른쪽 이미지 (H×W)
- `np.abs()`: 요소별 절댓값 계산
- `diff`: 두 이미지의 픽셀 차이 절댓값 (H×W)

### 4.4 구현 세부사항

**NumPy Broadcasting:**
```python
left_f - r_shift  # 같은 shape (H×W)끼리 요소별 빼기
```

**절댓값 계산:**
```python
np.abs(...)  # 모든 요소를 양수로 변환
```

**결과 저장:**
```python
cost_vol[:, :, d] = diff
```
- `cost_vol`의 d번째 슬라이스에 diff 저장
- 최종적으로 모든 d (0~D-1)에 대한 cost가 쌓임

**Invalid 영역 마킹 (line 32-33):**
```python
if d > 0:
    cost_vol[:, :d, d] = 1e6
```
- 왼쪽 d개 열은 shift로 인해 정보 없음 → 큰 값(1e6) 할당
- 나중에 disparity 선택 시 이 영역은 자동으로 제외됨

### 4.5 대안적 방법들

**SSD (Sum of Squared Differences):**
```python
diff = (left_f - r_shift) ** 2
```
- 큰 차이에 더 큰 패널티
- 노이즈에 더 민감

**Census Transform (robust to illumination change):**
```python
# 주변 픽셀과의 대소 관계를 비트 패턴으로 인코딩
# 조명 변화에 강건
```

**PA1에서는 SAD 사용** (단순하고 효과적)

### 4.6 디버깅 팁

- `diff`의 shape이 (H, W)인지 확인
- `diff`의 값 범위: 0 ~ 255 (grayscale 차이)
- `cost_vol[:, :, 0]`은 d=0일 때의 cost (shift 없음)
- `cost_vol[:, 0, :]`의 모든 d>0 값이 1e6인지 확인 (경계 처리)

---

## 5. TODO3: Cost Aggregation (Box Filter)

### 5.1 이론적 배경

**Cost Aggregation**은 픽셀 단위로 계산된 raw cost를 주변 영역과 합산하여 신뢰도를 높이는 단계입니다.

**왜 필요한가?**
- **노이즈 감소**: 개별 픽셀의 노이즈 영향 완화
- **Ambiguity 해결**: 텍스처가 없는 영역(예: 벽, 하늘)에서 주변 정보 활용
- **Smoothness 가정**: 인접 픽셀은 유사한 disparity를 가질 가능성 높음

**Box Filter:**
- 가장 단순한 aggregation 방법
- Window 내 모든 픽셀의 cost를 동일한 가중치로 평균화
- 수식: `agg_cost(x, y, d) = Σ cost(x', y', d)` for (x', y') in window

**수식:**
```
agg_cost = (1 / window_area) × Σ cost
```

OpenCV의 `cv2.boxFilter()`는 이를 효율적으로 구현합니다.

### 5.2 파이프라인 위치

```
cost_vol = build_cost_volume(left, right, max_disp)  ← (H×W×D)
    ↓
agg_cost_vol = aggregate_cost_volume_box(cost_vol, window_size=7)
    ↓
    각 d에 대해 (H×W) 슬라이스를 box filtering
```

### 5.3 모범 답안

**파일**: `stereo_matching.py`, 함수 `aggregate_cost_volume_box()` 내부 (line 43)

```python
# TODO3: aggregate cost volume
agg[:, :, d] = cv2.boxFilter(cost_vol[:, :, d], -1, k)
```

**설명:**
- `cost_vol[:, :, d]`: d번째 disparity의 cost map (H×W)
- `cv2.boxFilter(src, ddepth, ksize)`:
  - `src`: 입력 이미지 (H×W)
  - `ddepth=-1`: 출력이 입력과 같은 depth (float32)
  - `ksize=(window_size, window_size)`: 필터 커널 크기
- 결과: 각 픽셀 주변 window_size×window_size 영역의 평균값

### 5.4 구현 세부사항

**cv2.boxFilter 동작:**
```python
k = (window_size, window_size)  # 예: (7, 7)
cv2.boxFilter(img, -1, k)
```
- 각 픽셀 (x, y)를 중심으로 7×7 window 생성
- Window 내 49개 픽셀의 평균 계산
- 결과를 (x, y)에 저장
- 경계는 자동으로 처리 (replicate 또는 reflect)

**ddepth 파라미터:**
- `-1`: 입력과 같은 타입 유지 (float32 → float32)
- `cv2.CV_32F`: 명시적으로 float32 지정 (같은 효과)

**Loop 구조:**
```python
for d in range(D):
    agg[:, :, d] = cv2.boxFilter(cost_vol[:, :, d], -1, k)
```
- D개의 disparity에 대해 독립적으로 filtering
- 각 슬라이스는 2D 이미지처럼 처리

### 5.5 Window Size의 영향

**작은 window (예: 3×3):**
- 장점: 디테일 보존, 경계가 선명
- 단점: 노이즈에 취약, 텍스처 없는 영역에서 불안정

**큰 window (예: 15×15):**
- 장점: 노이즈 제거 강력, 부드러운 결과
- 단점: 경계가 흐려짐, 디테일 손실

**PA1 기본값: window_size=7**
- 중간 크기로 균형잡힌 결과
- 실험: 3, 5, 7, 11, 15 등 다양한 값 시도

### 5.6 대안적 Aggregation 방법들

**Gaussian Filter:**
```python
agg[:, :, d] = cv2.GaussianBlur(cost_vol[:, :, d], k, sigma)
```
- 중심에 높은 가중치, 거리에 따라 감소
- Box filter보다 부드러운 결과

**Bilateral Filter:**
```python
# Edge-aware filtering
# TODO6에서 다룸
```

**Guided Filter:**
```python
# Faster alternative to bilateral filter
```

**Semi-Global Matching (SGM):**
```python
# Path-wise cost aggregation
# 더 복잡하지만 성능 우수
```

### 5.7 디버깅 팁

- `agg`의 shape이 `cost_vol`과 같은지 확인: (H, W, D)
- `agg`의 값이 `cost_vol`보다 부드러운지 시각적 확인
- Window size가 홀수인지 확인 (중심 픽셀 정의 위해)
- `agg`의 값 범위가 합리적인지 확인 (0~255 정도)

---

## 6. TODO4: Disparity Selection (Winner-Takes-All)

### 6.1 이론적 배경

**Winner-Takes-All (WTA)**은 각 픽셀에서 cost가 최소인 disparity를 선택하는 단순하지만 효과적인 방법입니다.

**원리:**
- 각 픽셀 (x, y)에서 D개의 disparity 후보 중 선택
- 선택 기준: `d* = argmin_d cost(x, y, d)`
- "가장 잘 매칭되는 disparity를 선택"

**수식:**
```
disparity(x, y) = argmin_{d ∈ [0, D-1]} agg_cost_vol(x, y, d)
```

**WTA의 장단점:**
- 장점: 단순, 빠름, 대부분의 경우 합리적
- 단점: Occlusion, textureless 영역에서 오류 발생 가능

### 6.2 파이프라인 위치

```
agg_cost_vol = aggregate_cost_volume_box(cost_vol)  ← (H×W×D)
    ↓
disp = select_disparity(agg_cost_vol)  ← TODO4: argmin
    ↓
결과: Disparity map (H×W)
```

### 6.3 모범 답안

**파일**: `stereo_matching.py`, 함수 `select_disparity()` 내부 (line 48)

```python
# TODO4: select disparity
disp = np.argmin(agg_cost_vol, axis=2)
```

**설명:**
- `np.argmin(arr, axis=2)`: 3번째 축(disparity 축)에서 최솟값의 인덱스 반환
- `agg_cost_vol.shape = (H, W, D)`
- `axis=2`: D개의 disparity 중 선택
- `disp.shape = (H, W)`: 각 픽셀의 최적 disparity

### 6.4 구현 세부사항

**NumPy argmin:**
```python
np.argmin(arr, axis=k)
```
- `arr`의 k번째 축을 따라 최솟값의 인덱스 반환
- 반환값 shape: `arr.shape`에서 k번째 차원 제거

**예시:**
```python
cost = np.array([
    [10, 5, 8],  # pixel (0, 0)에서 d=0,1,2의 cost
    [3, 7, 2],   # pixel (0, 1)에서 d=0,1,2의 cost
])
np.argmin(cost, axis=1)  # [1, 2]
# (0, 0) → d=1 선택 (cost=5 최소)
# (0, 1) → d=2 선택 (cost=2 최소)
```

**3D 경우:**
```python
agg_cost_vol[y, x, :] = [c0, c1, ..., c63]  # 64개 disparity
disp[y, x] = argmin([c0, c1, ..., c63])
```

**타입 변환 (line 49):**
```python
disp = disp.astype(np.float32)
```
- `argmin`은 정수형 반환 (0~63)
- 후처리(filtering)를 위해 float32로 변환
- Sub-pixel refinement 가능

### 6.5 Sub-pixel Refinement (고급)

기본 WTA는 정수 단위 disparity만 반환. 더 정확한 깊이를 위해:

**Quadratic Fitting:**
```python
def sub_pixel_refinement(cost_vol, disp_int):
    H, W, D = cost_vol.shape
    disp_sub = disp_int.copy().astype(np.float32)

    for y in range(H):
        for x in range(W):
            d = int(disp_int[y, x])
            if 0 < d < D - 1:
                c0 = cost_vol[y, x, d - 1]
                c1 = cost_vol[y, x, d]
                c2 = cost_vol[y, x, d + 1]
                # Parabola fitting
                delta = (c0 - c2) / (2 * (c0 - 2*c1 + c2) + 1e-8)
                disp_sub[y, x] = d + delta

    return disp_sub
```

PA1에서는 **구현하지 않아도 됨** (선택사항).

### 6.6 디버깅 팁

- `disp`의 shape이 (H, W)인지 확인
- `disp`의 값 범위: 0 ~ (max_disp-1)
- Invalid 영역(왼쪽 경계)의 disparity가 이상한 값인지 확인
- 시각화: `cv2.normalize(disp, None, 0, 255, cv2.NORM_MINMAX)`

---

## 7. 기본 구현 검증

### 7.1 완성된 코드 (TODO1~TODO4)

**파일**: `stereo_matching.py`

```python
def build_cost_volume(left, right, max_disp=64):
    left_f  = left.astype(np.float32)
    right_f = right.astype(np.float32)
    h, w = left.shape
    D = max_disp
    cost_vol = np.zeros((h, w, D), np.float32)

    for d in range(D):
        # TODO1: image shift
        r_shift = shift_right_image(right_f, d)

        # TODO2: SAD
        diff = np.abs(left_f - r_shift)

        cost_vol[:, :, d] = diff

        if d > 0:
            cost_vol[:, :d, d] = 1e6

    return cost_vol

def aggregate_cost_volume_box(cost_vol, window_size=7):
    h, w, D = cost_vol.shape
    agg = np.zeros_like(cost_vol)
    k = (window_size, window_size)
    for d in range(D):
        # TODO3: aggregate cost volume
        agg[:, :, d] = cv2.boxFilter(cost_vol[:, :, d], -1, k)
    return agg

def select_disparity(agg_cost_vol):
    # TODO4: select disparity
    disp = np.argmin(agg_cost_vol, axis=2)
    disp = disp.astype(np.float32)
    return disp
```

### 7.2 실행 및 테스트

**기본 실행:**
```bash
cd /Users/wesley/Desktop/wooshikwon/computer_vision/PA1
source .venv/bin/activate
python stereo_matching.py
```

**출력:**
```
저장됨: output/reindeer_disparity.png
```

**결과 확인:**
- `output/reindeer_disparity.png` 생성됨
- Disparity map이 시각화되어 저장됨
- 어두운 영역: 멀리 있는 물체 (작은 disparity)
- 밝은 영역: 가까운 물체 (큰 disparity)

### 7.3 3D 시각화

**파일**: `visualize_disparity_3d.py`

경로 확인 (line 147-148):
```python
disparity_path = "output/reindeer_disparity.png"
rgb_path = "images/reindeer_left.png"
```

**실행:**
```bash
python visualize_disparity_3d.py
```

**결과:**
- 3D surface plot이 matplotlib 창으로 표시됨
- RGB 텍스처가 입혀진 깊이맵
- 마우스로 회전/확대 가능

### 7.4 파라미터 실험

**Max Disparity 변경:**
```python
disp, disp_vis = stereo_match(left_path, right_path,
                               max_disp=32,  # 64 → 32
                               window_size=7)
```
- 작은 max_disp: 먼 거리 추정 불가, 빠름
- 큰 max_disp: 넓은 범위 커버, 느림

**Window Size 변경:**
```python
disp, disp_vis = stereo_match(left_path, right_path,
                               max_disp=64,
                               window_size=3)  # 7 → 3
```
- 작은 window: 선명, 노이즈 많음
- 큰 window: 부드럽지만 경계 흐림

### 7.5 다른 이미지로 테스트

**파일**: `stereo_matching.py` (line 143-145)

```python
left_path  = "images/teddy_left.png"    # reindeer → teddy
right_path = "images/teddy_right.png"
output_path = "output/teddy_disparity.png"
```

**images/ 디렉토리의 스테레오 쌍들:**
- `reindeer_left.png`, `reindeer_right.png`
- `teddy_left.png`, `teddy_right.png`
- `cones_left.png`, `cones_right.png`
- `venus_left.png`, `venus_right.png`
- 등등

각 이미지 쌍으로 실험하여 알고리즘 성능 평가.

---

## 8. TODO6: Joint Bilateral Filter (고급)

> **참고**: 이 섹션의 더 상세한 설명은 `PA1/docs/PA1_JBF_detailed_explanation.md`를 참고하세요.

### 8.1 이론적 배경

#### 8.1.1 문제 상황: Box Filter의 한계

Box Filter로 cost를 aggregation하면 **물체 경계**에서 문제가 발생합니다:

```
물체 A (가까움, d=50)  |  배경 B (멀리, d=10)
━━━━━━━━━━━━━━━━━━━━┃━━━━━━━━━━━━━━━━━━
                    경계

Box Filter 적용 시:
- 경계 픽셀: 물체 A의 cost + 배경 B의 cost를 모두 섞음
- 결과: 잘못된 중간 disparity (d=30) 선택
- 문제: 경계가 흐려짐 (bleeding)
```

**해결책**: 물체 경계를 넘어 cost가 섞이지 않도록!

#### 8.1.2 Guide 이미지란?

**Guide 이미지**: 필터링할 때 **참고**하는 이미지

```python
# PA1에서의 사용
left_image = load_gray("reindeer_left.png")  # Guide 이미지
cost_vol = build_cost_volume(left, right)    # 필터링 대상

agg = joint_bilateral_filter(
    cost_vol,     # 이것을 부드럽게 하되
    left_image    # 이것을 참고해서 (경계 정보)
)
```

**왜 left_image를 guide로?**
- Left 이미지에는 **물체의 경계**가 명확히 보임
- 경계 = 밝기가 급격히 변하는 곳
- 예: 순록 몸통 (밝기 100) vs 배경 하늘 (밝기 200)

**Guide의 역할**:
```
"밝기가 비슷한 픽셀끼리만 cost를 섞어라!"
```

#### 8.1.3 공간 가우시안 (Gs) - "거리" 기반

**정의**: 픽셀 간 **물리적 거리**에 따른 가중치

```python
# 중심 픽셀 (x, y)에서 주변 픽셀 (x', y')까지의 거리
distance = √((x - x')² + (y - y')²)

# 공간 가우시안
Gs = exp(-distance² / (2 × sigma_s²))
```

**시각적 예시 (중심 픽셀 기준 5×5):**
```
Gs 가중치 (sigma_s=1.0):
  0.01  0.04  0.14  0.04  0.01
  0.04  0.14  0.61  0.14  0.04
  0.14  0.61 [1.00] 0.61  0.14  ← 중심이 가장 높음
  0.04  0.14  0.61  0.14  0.04
  0.01  0.04  0.14  0.04  0.01

특징: 거리가 가까울수록 가중치 높음 (대칭적)
```

#### 8.1.4 범위 가우시안 (Gr) - "픽셀 값 차이" 기반

**정의**: **Guide 이미지의 픽셀 값 차이**에 따른 가중치

```python
# 중심 픽셀의 guide 값
g_center = guide[y, x]  # 예: 0.2 (정규화된 밝기)

# 주변 픽셀의 guide 값
g_neighbor = guide[y', x']  # 예: 0.8

# 값 차이
value_diff = |g_center - g_neighbor|  # 0.6

# 범위 가우시안
Gr = exp(-value_diff² / (2 × sigma_r²))
```

**시각적 예시:**
```
Guide 이미지 (정규화 0-1):
  0.2  0.2  0.2 | 0.8  0.8  0.8
  0.2  0.2  [X] | 0.8  0.8  0.8   ← X=0.2
  0.2  0.2  0.2 | 0.8  0.8  0.8
  물체 A         | 배경 B
               ↑ 경계

Gr 가중치 (sigma_r=0.1, X=0.2 기준):
  1.0  1.0  1.0 | 0.0  0.0  0.0
  1.0  1.0 [1.0]| 0.0  0.0  0.0   ← 비슷한 값만 높음
  1.0  1.0  1.0 | 0.0  0.0  0.0

특징:
- 왼쪽 (0.2, 물체): 값 비슷 → Gr 높음 (1.0)
- 오른쪽 (0.8, 배경): 값 다름 → Gr 거의 0
- 경계를 넘으면 가중치 급감!
```

#### 8.1.5 Joint Bilateral Filter의 작동 원리

**최종 가중치 = Gs × Gr**

```python
weight(x, y, x', y') = Gs(거리) × Gr(guide 값 차이)

# 두 조건 모두 만족해야 높은 가중치:
# 1. 거리 가까워야 함 (Gs 높음)
# 2. Guide 값 비슷해야 함 (Gr 높음)
```

**경계 픽셀에서의 동작:**
```
물체 A (guide=0.2) | 배경 B (guide=0.8)
━━━━━━━━━━━━━━━━┃━━━━━━━━━━━━━━━━
                경계 픽셀 X

X의 왼쪽 픽셀들 (물체 A):
- Gs: 높음 (거리 가까움)
- Gr: 높음 (guide 값 비슷, 0.2≈0.2)
- 최종: 높음 → cost 섞임 ✅

X의 오른쪽 픽셀들 (배경 B):
- Gs: 높음 (거리 가까움)
- Gr: 거의 0 (guide 값 다름, 0.2≠0.8)
- 최종: 거의 0 → cost 안 섞임 ❌

결과: 물체 A의 cost만 사용 → 경계 보존!
```

**수식:**
```
agg_cost(x, y, d) = Σ cost(x', y', d) × Gs × Gr / W

여기서:
- cost(x', y', d): 주변 픽셀의 cost 값 (필터링 대상)
- Gs = exp(-픽셀거리² / 2σ_s²)
- Gr = exp(-guide값차이² / 2σ_r²)  ← Guide 이미지 참고!
- W = Σ(Gs × Gr): 정규화 상수
```

**핵심**:
1. Cost volume을 부드럽게 하되
2. Guide (left 이미지)를 참고
3. Guide에서 값이 비슷한 픽셀끼리만 섞음
4. 경계를 넘으면 값이 다르므로 안 섞임

### 8.2 파이프라인 위치

```
build_cost_volume(left, right, max_disp)  ← (H×W×D)
    ↓
TODO6: agg_cost_vol = aggregate_cost_volume_joint_bilateral_numpy(
           cost_vol, left, win_radius, sigma_s, sigma_r)
    ↓
    (기존 box filter 대신 사용)
    ↓
select_disparity(agg_cost_vol)
```

### 8.3 모범 답안

**파일**: `stereo_matching.py`, 함수 `stereo_match()` 내부 (line 127-128)

TODO6 주석을 해제하고 다음과 같이 수정:

```python
# TODO6: Joint Bilateral Filter (채우지 않아도 코드는 실행 가능)
agg_cost_vol = aggregate_cost_volume_joint_bilateral_numpy(
    cost_vol, left, win_radius=3, sigma_s=3.0, sigma_r=0.1
)

# 기존 box filter는 주석 처리
# agg_cost_vol = aggregate_cost_volume_box(cost_vol, window_size=window_size)
```

**설명:**
- `cost_vol`: 원본 cost volume (H×W×D)
- `left`: guide 이미지 (grayscale, H×W)
- `win_radius=3`: 7×7 window (2*3+1=7)
- `sigma_s=3.0`: 공간 가우시안 표준편차
- `sigma_r=0.1`: 범위 가우시안 표준편차 (normalized 0-1 scale)

### 8.4 구현 세부사항

**이미 구현된 함수 (line 76-85):**
```python
def aggregate_cost_volume_joint_bilateral_numpy(cost_vol, guide_gray,
                                                 win_radius=3, sigma_s=3.0, sigma_r=0.1):
    guide = (guide_gray.astype(np.float32) / 255.0).copy()  # 정규화
    H, W, D = cost_vol.shape
    out = np.empty_like(cost_vol)
    for d in range(D):
        out[:, :, d] = joint_bilateral_slice_numpy(
            cost_vol[:, :, d].astype(np.float32),
            guide, win_radius=win_radius, sigma_s=sigma_s, sigma_r=sigma_r
        )
    return out
```

**핵심 함수: `joint_bilateral_slice_numpy()` (line 52-74):**
```python
def joint_bilateral_slice_numpy(src, guide, win_radius=3, sigma_s=3.0, sigma_r=0.1):
    H, W = src.shape
    out = np.zeros_like(src)

    ksize = 2 * win_radius + 1
    ys, xs = np.mgrid[-win_radius:win_radius+1, -win_radius:win_radius+1]
    Gs = np.exp(-(xs**2 + ys**2) / (2 * sigma_s**2)).astype(np.float32)  # 공간 가우시안

    pad = win_radius
    src_p = np.pad(src, pad, mode='reflect')
    gui_p = np.pad(guide, pad, mode='reflect')

    for y in range(H):
        for x in range(W):
            g0 = gui_p[y+pad, x+pad]  # 중심 픽셀의 guide 값
            src_patch = src_p[y:y+ksize, x:x+ksize]
            gui_patch = gui_p[y:y+ksize, x:x+ksize]
            Gr = np.exp(-((gui_patch - g0)**2) / (2 * sigma_r**2))  # 범위 가우시안
            Wgt = Gs * Gr  # 공간 × 범위
            s = (src_patch * Wgt).sum()
            w = Wgt.sum() + 1e-8  # 안정성을 위한 작은 값
            out[y, x] = s / w  # 가중 평균
    return out
```

### 8.5 파라미터 조정

**win_radius:**
- 작을수록 (1, 2): 빠르지만 덜 부드러움
- 클수록 (5, 7): 느리지만 더 부드러움

**sigma_s (공간):**
- 작을수록: 가까운 픽셀만 영향
- 클수록: 넓은 범위 영향

**sigma_r (범위):**
- 작을수록: edge 보존 강함 (값이 조금만 달라도 가중치 급감)
- 클수록: edge 보존 약함 (일반 가우시안에 가까움)

**추천 값:**
```python
# Sharp edges 보존 (경계 선명)
win_radius=3, sigma_s=3.0, sigma_r=0.05

# Balanced (기본)
win_radius=3, sigma_s=3.0, sigma_r=0.1

# Smooth (부드러운 결과)
win_radius=5, sigma_s=5.0, sigma_r=0.2
```

### 8.6 Box Filter vs. Joint Bilateral Filter

**Box Filter:**
- 장점: 매우 빠름 (O(1) per pixel with integral image)
- 단점: Edge에서 bleeding (경계가 흐려짐)

**Joint Bilateral Filter:**
- 장점: Edge 보존 (물체 경계 선명)
- 단점: 느림 (O(window_size²) per pixel)

**PA1에서 선택:**
- 기본 점수: Box filter로 충분
- 고급 점수: JBF로 품질 향상 (속도는 느림)

### 8.7 디버깅 팁

- `guide` 이미지가 0-1 범위로 정규화되었는지 확인
- `sigma_r`이 너무 크면 일반 가우시안과 차이 없음
- `sigma_r`이 너무 작으면 거의 filtering 안 됨
- 실행 시간: 수십 초 이상 소요 (정상)

---

## 9. TODO7: Weighted Median Filter (고급)

> **참고**: 이 섹션의 더 상세한 설명은 `PA1/docs/PA1_WMF_detailed_explanation.md`를 참고하세요.

### 9.1 이론적 배경

#### 9.1.1 문제 상황: Disparity Map의 Outlier

Disparity selection 후에도 여전히 **노이즈**와 **이상치(outlier)**가 남아있습니다:

```
이상적: 물체 = 50 50 50 50 50
실제:   물체 = 50 50 [3] 50 50  ← Outlier!

원인:
- Textureless 영역 (텍스처 없는 벽, 하늘)
- Occlusion (가려진 영역)
- 반복 패턴
- 센서 노이즈
```

**Mean/Gaussian Filter의 문제:**
```python
값: [50, 50, 3, 50, 50]
평균: (50+50+3+50+50) / 5 = 40.6
      ↑ Outlier 3이 평균을 크게 왜곡! ❌
```

**해결책**: Outlier에 강건한 **Median** 사용!

#### 9.1.2 Median Filter란?

**정의**: 값들을 정렬했을 때 **중간에 위치한 값**

```python
값: [50, 50, 3, 50, 50]
정렬: [3, 50, 50, 50, 50]
Median:      ↑ 50

Outlier 3은 median에 영향 없음! ✅
```

**Median vs Mean:**
```
정상 + Outlier: [10, 10, 10, 10, 10, 100]

Mean: 25 ← 왜곡됨
Median: 10 ← 정확!
```

**Median의 장점**: Outlier에 **강건(robust)**

#### 9.1.3 일반 Median의 한계

```
물체 A (d=50) | 배경 B (d=10)
━━━━━━━━━━━━┃━━━━━━━━━━━━
           경계

경계 픽셀에서 3×3 median:
값: [50, 50, 50, 50, X, 10, 10, 10, 10]
정렬: [10, 10, 10, 10, 50, 50, 50, 50, X]
Median:                ↑ 10 또는 50 (불안정)

문제: 경계를 무시하고 물체+배경 값 모두 섞음
```

**해결책**: Guide 이미지로 가중치 → **Weighted Median**

#### 9.1.4 Weighted Median이란?

**정의**: 각 값에 **가중치**를 부여하여 계산한 중간값

**핵심 아이디어:**
```
일반 Median: 모든 값이 동등한 1표
Weighted Median: 중요한 값은 더 많은 표
```

**알고리즘:**
1. 값들을 정렬
2. 가중치의 **누적합(cumulative sum)** 계산
3. 누적합이 **전체의 50%**가 되는 지점의 값 선택

**예시:**
```python
값:      [10, 20, 30, 40]
가중치:  [0.1, 0.3, 0.4, 0.2]

Step 1: 정렬 (이미 정렬됨)
Step 2: 누적 가중치
  10: 0.1        (10%)
  20: 0.1+0.3=0.4 (40%)
  30: 0.4+0.4=0.8 (80%)  ← 50% 넘는 첫 지점!
  40: 0.8+0.2=1.0 (100%)

Step 3: 50% 지점 = 0.5
  → 0.5는 0.4와 0.8 사이
  → Weighted Median = 30 ✅
```

#### 9.1.5 Guide 이미지의 역할

**Weighted Median에서도 Guide 사용:**
```python
weighted_median_filter(
    disparity,    # 필터링 대상
    left_image    # Guide (경계 정보)
)
```

**가중치 계산 = Bilateral 방식:**
```python
weight = Gs × Gr

Gs: 공간 가우시안 (거리 기반)
Gr: 범위 가우시안 (guide 값 차이 기반)
```

**경계 픽셀에서:**
```
물체 A (guide=0.2) | 배경 B (guide=0.8)
━━━━━━━━━━━━━━━━┃━━━━━━━━━━━━━━━━
                경계 픽셀 X

X의 왼쪽 (물체 A):
- guide 값 비슷 (0.2≈0.2) → Gr 높음 → 가중치 높음

X의 오른쪽 (배경 B):
- guide 값 다름 (0.2≠0.8) → Gr 낮음 → 가중치 낮음

결과: 물체 A의 disparity 값들이 median 결정에 주도권!
```

#### 9.1.6 Weighted Median의 이중 효과

**1. 경계 보존 (Guide 활용)**
- 같은 물체 내 값들만 median 계산에 큰 영향
- 다른 물체 값은 가중치 낮아서 영향 최소

**2. Outlier 제거 (Median 본질)**
- 극단값은 median에 영향 없음
- 다수의 정상 값이 median 결정

**예시:**
```
Disparity (경계 픽셀 주변):
  50  50  50
  50 [X]  10
  10  10  10

일반 Median:
  정렬: [10, 10, 10, 10, 50, 50, 50, 50, X]
  Median:                ↑ 10 또는 50 (불안정)

Weighted Median (X가 물체 쪽):
  물체 값들 (50): 가중치 높음
  배경 값들 (10): 가중치 낮음
  → Weighted Median = 50 ✅
```

**수식:**
```
WM(x, y) = weighted_median { d(x', y') : weight(x', y') }

여기서:
- d(x', y'): 주변 픽셀의 disparity 값
- weight = Gs × Gr
  - Gs = exp(-거리² / 2σ_s²)
  - Gr = exp(-guide값차이² / 2σ_r²)
- weighted median: 가중치 누적합이 50%가 되는 지점의 값
```

### 9.2 파이프라인 위치

```
disp = select_disparity(agg_cost_vol)  ← (H×W)
    ↓
TODO7: disp = weighted_median_disparity_numpy(disp, left,
                  win_radius=3, sigma_s=3.0, sigma_r=0.08)
    ↓
    (기존 disparity를 refine)
    ↓
disp_vis = cv2.normalize(disp, ...)
```

### 9.3 모범 답안

**파일**: `stereo_matching.py`, 함수 `stereo_match()` 내부 (line 135-136)

TODO7 주석 해제:

```python
# TODO7: Weighted Median Filter (채우지 않아도 코드는 실행 가능)
disp = weighted_median_disparity_numpy(disp, left, win_radius=3, sigma_s=3.0, sigma_r=0.08)
```

**설명:**
- `disp`: 기존 disparity map (H×W)
- `left`: guide 이미지 (grayscale, H×W)
- `win_radius=3`: 7×7 window
- `sigma_s=3.0`: 공간 가우시안
- `sigma_r=0.08`: 범위 가우시안 (JBF보다 약간 작게)

### 9.4 구현 세부사항

**이미 구현된 함수 (line 87-118):**
```python
def weighted_median_disparity_numpy(disp, guide_gray, win_radius=3, sigma_s=3.0, sigma_r=0.1):
    disp = disp.astype(np.float32)
    guide = guide_gray.astype(np.float32) / 255.0
    H, W = disp.shape
    out = np.zeros_like(disp)

    k = 2*win_radius + 1
    ys, xs = np.mgrid[-win_radius:win_radius+1, -win_radius:win_radius+1]
    Gs = np.exp(-(xs**2 + ys**2) / (2 * sigma_s**2))  # 공간 가우시안

    pad = win_radius
    d_p = np.pad(disp, pad, mode='reflect')
    g_p = np.pad(guide, pad, mode='reflect')

    for y in range(H):
        for x in range(W):
            g0 = g_p[y+pad, x+pad]  # 중심 픽셀의 guide 값
            d_patch = d_p[y:y+k, x:x+k]  # 주변 disparity 값들
            g_patch = g_p[y:y+k, x:x+k]  # 주변 guide 값들

            Gr = np.exp(-((g_patch - g0)**2) / (2 * sigma_r**2))  # 범위 가우시안
            Wgt = (Gs * Gr).reshape(-1)  # 1D로 flatten
            Vals = d_patch.reshape(-1)

            # Weighted median 계산
            order = np.argsort(Vals)  # 값 정렬
            w_sorted = Wgt[order]     # 가중치도 같은 순서로
            v_sorted = Vals[order]    # 정렬된 값들
            csum = np.cumsum(w_sorted)  # 누적합
            half = csum[-1] * 0.5       # 전체 가중치의 50%
            idx = np.searchsorted(csum, half)  # 50% 지점 찾기
            out[y, x] = v_sorted[min(idx, v_sorted.size-1)]
    return out
```

**핵심 알고리즘 단계별 설명:**

**Step 1: 주변 disparity 값과 가중치 수집**
```python
# 7×7 window의 49개 값
d_patch = disp[y:y+7, x:x+7]      # Disparity 값들
g_patch = guide[y:y+7, x:x+7]     # Guide 값들

# Bilateral 가중치 계산
Gs = exp(-거리² / 2σ_s²)          # 공간 가우시안
Gr = exp(-(g_patch-g0)² / 2σ_r²)  # 범위 가우시안
weight = Gs × Gr
```

**Step 2: 값으로 정렬**
```python
order = np.argsort(Vals)         # 정렬 인덱스
v_sorted = Vals[order]           # 정렬된 disparity
w_sorted = Wgt[order]            # 같은 순서로 가중치 정렬
```

**Step 3: 가중치 누적합 계산**
```python
csum = np.cumsum(w_sorted)       # [w1, w1+w2, w1+w2+w3, ...]
half = csum[-1] * 0.5            # 전체의 50%
```

**Step 4: 50% 지점의 값 선택**
```python
idx = np.searchsorted(csum, half)  # 50% 넘는 첫 인덱스
result = v_sorted[idx]              # Weighted Median!
```

**구체적 예시:**
```
입력:
Disparity 값: [50, 50, 3, 50, 50]  ← 중간에 outlier
가중치:       [0.2, 0.3, 0.05, 0.3, 0.15]

Step 1: 정렬
값:           [3,    50,   50,   50,   50]
가중치:       [0.05, 0.2,  0.3,  0.3,  0.15]

Step 2: 누적 가중치
값:           [3,    50,   50,   50,   50]
가중치:       [0.05, 0.2,  0.3,  0.3,  0.15]
누적:         [0.05, 0.25, 0.55, 0.85, 1.0]
              5%    25%   55%   85%   100%
                          ↑
                      첫 50% 넘음

Step 3: 결과
50% 지점 = 0.5
누적 0.55가 첫 번째로 0.5 넘음
→ Weighted Median = 50 ✅

Outlier 3은 가중치 낮아서 무시됨!
```

**경계 픽셀에서의 동작:**
```
Disparity:
  50  50  50
  50 [X]  10
  10  10  10

Guide (X가 물체 쪽, guide=0.2):
  0.2  0.2  0.2
  0.2 [X]  0.8
  0.8  0.8  0.8

가중치 (Bilateral):
  물체 (50): 높음 (0.8)
  배경 (10): 낮음 (0.01)

Weighted Median 계산:
값:     [10,   10,   10,   10,   50,  50,  50,  50,  X]
가중치: [0.01, 0.01, 0.01, 0.01, 0.8, 0.8, 0.8, 0.8, 1.0]
누적:   [0.01, 0.02, 0.03, 0.04, 0.84, 1.64, 2.44, 3.24, 4.24]

전체: 4.24
50%: 2.12
→ 누적 2.44가 첫 50% 넘음
→ Weighted Median = 50 ✅

물체의 disparity 보존!
```

### 9.5 파라미터 조정

**sigma_r (JBF vs. WMF):**
- JBF에서는 `sigma_r=0.1` (cost aggregation)
- WMF에서는 `sigma_r=0.08` (약간 작게)
- 이유: Disparity는 이미 어느 정도 정확하므로 edge 보존 더 강하게

**실험:**
```python
# Edge 강하게 보존
disp = weighted_median_disparity_numpy(disp, left,
           win_radius=3, sigma_s=3.0, sigma_r=0.05)

# 부드러운 결과
disp = weighted_median_disparity_numpy(disp, left,
           win_radius=5, sigma_s=5.0, sigma_r=0.15)
```

### 9.6 Weighted Median의 장점

#### 9.6.1 Outlier 제거 (Robustness)

**Median의 본질적 강건성:**
```
정상 값: [10, 10, 10, 10, 10]
Outlier 추가: [10, 10, 10, 10, 10, 100]

Mean (평균):
  (10×5 + 100) / 6 = 25  ← 크게 왜곡!

Median (중간값):
  정렬: [10, 10, 10, 10, 10, 100]
  중간:          ↑↑ (10+10)/2 = 10  ← 정확!

핵심: Median은 순서만 보므로 극단값 영향 최소
```

**실제 예시 (Salt-and-pepper noise):**
```
원본: 10  10  10  10  10
노이즈: 10 255  10 255  10

Mean: (10+255+10+255+10) / 5 = 108  ← 엉망
Median: [10, 10, 10, 255, 255] → 10  ← 복원!
```

#### 9.6.2 경계 보존 (Edge Preservation)

**Bilateral 가중치 효과:**
```
경계 픽셀에서:
  물체 값들: 가중치 높음 → median 결정에 큰 영향
  배경 값들: 가중치 낮음 → median 결정에 작은 영향

결과: 물체의 정확한 disparity 보존
```

#### 9.6.3 Box Filter / JBF / WMF 비교

| 필터 | 경계 보존 | Outlier 제거 | 속도 | 품질 |
|------|----------|-------------|------|------|
| **Box Filter** | ❌ 흐려짐 | ❌ 민감 | ⚡⚡⚡ 매우 빠름 | ⭐⭐ 보통 |
| **JBF** | ✅ 선명 | ⚠️ 약간 민감 | 🐢 느림 | ⭐⭐⭐ 좋음 |
| **WMF** | ✅ 선명 | ✅ 강건 | 🐌 매우 느림 | ⭐⭐⭐⭐ 최고 |

**조합 사용 (권장):**
```
1. JBF로 cost aggregation → 경계 보존
2. WMF로 disparity refinement → outlier 제거
→ 최고 품질!
```

### 9.7 디버깅 팁

- WMF는 disparity에 적용 (cost volume 아님)
- 실행 시간: 수십 초 이상 소요 (정상)
- 결과: 기존 disparity보다 부드럽고 이상치 감소
- 시각적 비교: WMF 전후 비교 이미지 생성

---

## 10. 최종 코드 및 결과

### 10.1 완전한 stereo_matching.py

**모든 TODO 구현 완료:**

```python
import cv2
import numpy as np

def load_gray(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return img

def shift_right_image(right, d):
    if d == 0:
        return right
    h, w = right.shape
    shifted = np.zeros_like(right)
    shifted[:, d:] = right[:, :w-d]
    return shifted

def build_cost_volume(left, right, max_disp=64):
    left_f  = left.astype(np.float32)
    right_f = right.astype(np.float32)
    h, w = left.shape
    D = max_disp
    cost_vol = np.zeros((h, w, D), np.float32)

    for d in range(D):
        # TODO1: image shift
        r_shift = shift_right_image(right_f, d)

        # TODO2: SAD
        diff = np.abs(left_f - r_shift)

        cost_vol[:, :, d] = diff

        if d > 0:
            cost_vol[:, :d, d] = 1e6

    return cost_vol

def aggregate_cost_volume_box(cost_vol, window_size=7):
    h, w, D = cost_vol.shape
    agg = np.zeros_like(cost_vol)
    k = (window_size, window_size)
    for d in range(D):
        # TODO3: aggregate cost volume
        agg[:, :, d] = cv2.boxFilter(cost_vol[:, :, d], -1, k)
    return agg

def select_disparity(agg_cost_vol):
    # TODO4: select disparity
    disp = np.argmin(agg_cost_vol, axis=2)
    disp = disp.astype(np.float32)
    return disp

def joint_bilateral_slice_numpy(src, guide, win_radius=3, sigma_s=3.0, sigma_r=0.1):
    H, W = src.shape
    out = np.zeros_like(src)

    ksize = 2 * win_radius + 1
    ys, xs = np.mgrid[-win_radius:win_radius+1, -win_radius:win_radius+1]
    Gs = np.exp(-(xs**2 + ys**2) / (2 * sigma_s**2)).astype(np.float32)

    pad = win_radius
    src_p = np.pad(src, pad, mode='reflect')
    gui_p = np.pad(guide, pad, mode='reflect')

    for y in range(H):
        for x in range(W):
            g0 = gui_p[y+pad, x+pad]
            src_patch = src_p[y:y+ksize, x:x+ksize]
            gui_patch = gui_p[y:y+ksize, x:x+ksize]
            Gr = np.exp(-((gui_patch - g0)**2) / (2 * sigma_r**2)).astype(np.float32)
            Wgt = Gs * Gr
            s = (src_patch * Wgt).sum()
            w = Wgt.sum() + 1e-8
            out[y, x] = s / w
    return out

def aggregate_cost_volume_joint_bilateral_numpy(cost_vol, guide_gray, win_radius=3, sigma_s=3.0, sigma_r=0.1):
    guide = (guide_gray.astype(np.float32) / 255.0).copy()
    H, W, D = cost_vol.shape
    out = np.empty_like(cost_vol)
    for d in range(D):
        out[:, :, d] = joint_bilateral_slice_numpy(
            cost_vol[:, :, d].astype(np.float32),
            guide, win_radius=win_radius, sigma_s=sigma_s, sigma_r=sigma_r
        )
    return out

def weighted_median_disparity_numpy(disp, guide_gray, win_radius=3, sigma_s=3.0, sigma_r=0.1):
    disp = disp.astype(np.float32)
    guide = guide_gray.astype(np.float32) / 255.0
    H, W = disp.shape
    out = np.zeros_like(disp)

    k = 2*win_radius + 1
    ys, xs = np.mgrid[-win_radius:win_radius+1, -win_radius:win_radius+1]
    Gs = np.exp(-(xs**2 + ys**2) / (2 * sigma_s**2)).astype(np.float32)

    pad = win_radius
    d_p = np.pad(disp, pad, mode='reflect')
    g_p = np.pad(guide, pad, mode='reflect')

    for y in range(H):
        for x in range(W):
            g0 = g_p[y+pad, x+pad]
            d_patch = d_p[y:y+k, x:x+k]
            g_patch = g_p[y:y+k, x:x+k]

            Gr = np.exp(-((g_patch - g0)**2) / (2 * sigma_r**2)).astype(np.float32)
            Wgt = (Gs * Gr).reshape(-1)
            Vals = d_patch.reshape(-1)

            order = np.argsort(Vals)
            w_sorted = Wgt[order]
            v_sorted = Vals[order]
            csum = np.cumsum(w_sorted)
            half = csum[-1] * 0.5
            idx = np.searchsorted(csum, half)
            out[y, x] = v_sorted[min(idx, v_sorted.size-1)]
    return out

def stereo_match(left_path, right_path,
                 max_disp=64, window_size=7,
                 use_jbf=False, use_wmf=False):
    """
    스테레오 매칭 메인 함수

    use_jbf: True이면 Joint Bilateral Filter 사용 (TODO6)
    use_wmf: True이면 Weighted Median Filter 사용 (TODO7)
    """
    left  = load_gray(left_path)
    right = load_gray(right_path)

    cost_vol = build_cost_volume(left, right, max_disp=max_disp)

    # TODO6: Joint Bilateral Filter (선택)
    if use_jbf:
        agg_cost_vol = aggregate_cost_volume_joint_bilateral_numpy(
            cost_vol, left, win_radius=3, sigma_s=3.0, sigma_r=0.1
        )
    else:
        agg_cost_vol = aggregate_cost_volume_box(cost_vol, window_size=window_size)

    disp = select_disparity(agg_cost_vol)

    # TODO7: Weighted Median Filter (선택)
    if use_wmf:
        disp = weighted_median_disparity_numpy(disp, left, win_radius=3, sigma_s=3.0, sigma_r=0.08)

    disp_vis = cv2.normalize(disp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return disp, disp_vis

if __name__ == "__main__":
    left_path  = "images/reindeer_left.png"
    right_path = "images/reindeer_right.png"
    output_path = "output/reindeer_disparity.png"

    # 기본 버전 (Box filter only)
    disp_basic, disp_basic_vis = stereo_match(
        left_path, right_path,
        max_disp=64, window_size=7,
        use_jbf=False, use_wmf=False
    )
    cv2.imwrite(output_path, disp_basic_vis)
    print("저장됨 (기본): " + output_path)

    # 고급 버전 (JBF + WMF) - 선택사항
    # disp_advanced, disp_advanced_vis = stereo_match(
    #     left_path, right_path,
    #     max_disp=64, window_size=7,
    #     use_jbf=True, use_wmf=True
    # )
    # cv2.imwrite("output/reindeer_disparity_advanced.png", disp_advanced_vis)
    # print("저장됨 (고급): output/reindeer_disparity_advanced.png")
```

### 10.2 실행 가이드

**1. 기본 실행 (TODO1-4만):**
```bash
python stereo_matching.py
```
- Box filter 사용
- 빠른 실행 (수 초)
- 결과: `output/reindeer_disparity.png`

**2. 고급 실행 (TODO6-7 포함):**

코드 수정 (line 143-151 주석 해제):
```python
disp_advanced, disp_advanced_vis = stereo_match(
    left_path, right_path,
    max_disp=64, window_size=7,
    use_jbf=True, use_wmf=True
)
cv2.imwrite("output/reindeer_disparity_advanced.png", disp_advanced_vis)
print("저장됨 (고급): output/reindeer_disparity_advanced.png")
```

실행:
```bash
python stereo_matching.py
```
- Joint Bilateral Filter + Weighted Median Filter 사용
- 느린 실행 (수 분)
- 결과: 기본 + 고급 두 버전 생성

**3. 3D 시각화:**
```bash
python visualize_disparity_3d.py
```

### 10.3 결과 비교

**기대 결과:**

**Box Filter (기본):**
- 부드러운 disparity map
- 경계에서 약간 bleeding 발생
- 빠른 실행
- 대부분의 영역에서 합리적인 깊이 추정

**JBF (고급):**
- 경계가 더 선명
- 물체와 배경 사이 disparity가 섞이지 않음
- 텍스처 영역에서 디테일 보존

**WMF (고급):**
- Outlier 제거 (잘못된 disparity 수정)
- 전체적으로 더 일관된 결과
- Textureless 영역의 노이즈 감소

### 10.4 성능 평가

**정량적 평가 (Extra Credit에서 다룸):**
- Ground truth disparity와 비교
- 오차 계산: MAE, RMSE, percentage of bad pixels
- 다양한 파라미터 조합 실험

**정성적 평가:**
- 시각적으로 자연스러운가?
- 물체 경계가 선명한가?
- 텍스처 없는 영역(벽, 하늘)에서도 합리적인가?
- 이상치(outlier)가 많은가?

### 10.5 리포트 작성 가이드

PA1 리포트에 포함할 내용 (5점):

**1. 구현 설명 (2점):**
- TODO1-4 구현 방법 설명
- 선택한 파라미터 (max_disp, window_size) 설명
- TODO6-7 구현 여부 및 방법

**2. 결과 분석 (2점):**
- 각 이미지 쌍에 대한 결과 이미지 첨부
- 정성적 평가 (어떤 부분이 잘 되고/안 되는지)
- 파라미터 변화에 따른 결과 비교
- 3D 시각화 결과 (선택)

**3. 고찰 (1점):**
- 알고리즘의 장단점
- 실패 사례 분석 (예: textureless 영역, occlusion)
- 개선 방향 제안

**리포트 구조 예시:**
```markdown
# PA1: Stereo Matching 리포트

## 1. 구현 방법
### 1.1 이미지 시프팅 (TODO1)
- ...

### 1.2 SAD 계산 (TODO2)
- ...

...

## 2. 실험 결과
### 2.1 Reindeer 이미지
- 결과 이미지
- 분석

### 2.2 파라미터 실험
- window_size 변화
- max_disp 변화

## 3. 고찰
- 장단점
- 개선 방향
```

### 10.6 추가 도전 (Extra Credit)

**Graph-Cuts (최대 5점):**
- MRF(Markov Random Field) 기반 글로벌 최적화
- Energy minimization 문제로 formulation
- 라이브러리: `pygco` 또는 직접 구현

**Custom Dataset (최대 3점):**
- 본인이 촬영한 스테레오 이미지 쌍 사용
- Calibration 및 rectification 필요
- 실제 환경에서의 성능 평가

---

## 부록 A: 자주 묻는 질문

**Q1: Cost volume의 invalid 영역을 왜 1e6으로 설정하나요?**
A: Disparity selection에서 argmin을 사용하므로, 큰 값을 할당하면 해당 disparity가 선택되지 않습니다. 0이나 작은 값을 넣으면 잘못된 disparity가 선택될 수 있습니다.

**Q2: Box filter의 window_size는 홀수여야 하나요?**
A: OpenCV의 boxFilter는 홀수/짝수 모두 가능하지만, 홀수가 권장됩니다. 중심 픽셀이 명확히 정의되기 때문입니다.

**Q3: JBF와 WMF를 동시에 사용하면 효과가 더 좋나요?**
A: 일반적으로 그렇습니다. JBF는 cost aggregation 단계에서, WMF는 disparity refinement 단계에서 작용하므로 상호보완적입니다.

**Q4: 실행이 너무 느린데 어떻게 하나요?**
A:
- 기본 버전(Box filter)만 사용하면 빠릅니다.
- JBF/WMF는 느리지만 더 좋은 결과를 제공합니다.
- 최적화: Numba, Cython, C++ 등으로 가속 가능 (선택사항)

**Q5: Disparity가 이상하게 나오는데 어떻게 디버깅하나요?**
A:
1. Cost volume 시각화: `cv2.imshow("cost", cost_vol[:, :, d])`
2. 각 TODO 단계별로 결과 확인
3. Invalid 영역 마킹 확인
4. 이미지가 제대로 로딩되었는지 확인

---

## 부록 B: 참고 자료

**논문:**
1. Scharstein & Szeliski (2002) - "A Taxonomy and Evaluation of Dense Two-Frame Stereo Correspondence Algorithms"
2. Tomasi & Manduchi (1998) - "Bilateral Filtering for Gray and Color Images"
3. Boykov et al. (2001) - "Fast Approximate Energy Minimization via Graph Cuts"

**온라인 자료:**
- Middlebury Stereo Benchmark: https://vision.middlebury.edu/stereo/
- OpenCV Stereo Documentation: https://docs.opencv.org/

**추가 학습:**
- Semi-Global Matching (SGM)
- Deep Learning Stereo (예: PSMNet, GANet)
- Multi-view Stereo (MVS)

---

**PA1 완료를 축하합니다!** 질문이 있으면 조교에게 문의하세요.
