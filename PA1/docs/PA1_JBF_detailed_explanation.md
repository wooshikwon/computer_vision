# Joint Bilateral Filter 완전 이해 가이드

## 목차
1. [문제 상황: 왜 필요한가?](#1-문제-상황-왜-필요한가)
2. [Guide 이미지란?](#2-guide-이미지란)
3. [일반 필터 vs Bilateral Filter](#3-일반-필터-vs-bilateral-filter)
4. [공간 가우시안 (Gs)](#4-공간-가우시안-gs)
5. [범위 가우시안 (Gr)](#5-범위-가우시안-gr)
6. [Joint Bilateral Filter](#6-joint-bilateral-filter)
7. [PA1에서의 적용](#7-pa1에서의-적용)
8. [실전 예시](#8-실전-예시)

---

## 1. 문제 상황: 왜 필요한가?

### 1.1 Box Filter의 문제

스테레오 매칭에서 cost를 aggregation할 때 **Box Filter**를 사용하면:

```
물체 A (가까움)   |  배경 B (멀리)
disparity=50   |  disparity=10
━━━━━━━━━━━━━━━┃━━━━━━━━━━━━━━━
              경계
```

**Box Filter 적용 시:**

```
경계 근처 픽셀:
- 물체 A의 cost (d=50)
- 배경 B의 cost (d=10)
→ 두 개가 섞여서 평균냄 → disparity=30 (잘못된 값!)
```

**문제**: 경계에서 disparity가 **bleeding** (흐려짐) 발생

### 1.2 이상적인 해결책

```
경계 근처 픽셀에서:
- 같은 물체의 cost만 평균내고 싶음 ✅
- 다른 물체의 cost는 제외하고 싶음 ✅
```

**어떻게?** → **물체 경계 정보를 활용**

---

## 2. Guide 이미지란?

### 2.1 정의

**Guide 이미지**: 필터링할 때 **참고**하는 이미지

- Filtering 대상: Cost volume (우리가 부드럽게 하고 싶은 것)
- Guide: 원본 이미지 (물체 경계 정보를 알려주는 것)

### 2.2 PA1에서의 Guide 이미지

```python
left_image = load_gray("reindeer_left.png")  # 왼쪽 원본 이미지
cost_vol = build_cost_volume(left, right)    # Cost volume

# left_image를 guide로 사용
agg = aggregate_cost_volume_joint_bilateral_numpy(
    cost_vol,     # 필터링 대상
    left_image,   # Guide (참고용)
    ...
)
```

**왜 left_image를 guide로?**
- Left 이미지에는 **물체의 경계**가 명확히 보임
- 경계 = 밝기가 급격히 변하는 곳
- 이 정보로 "여기는 다른 물체니까 섞지 마!" 판단

### 2.3 Guide 이미지의 역할

**시각적 예시:**

```
Left 이미지 (Guide):
  50  50  50 | 200 200 200    ← 밝기 값
  물체 A      | 배경 B
              ↑
           경계 (밝기 급변)

Cost volume (필터링 대상):
  [cost_A]  [cost_A] | [cost_B] [cost_B]
```

**Guide가 알려주는 것:**
- "50과 50은 비슷 → 같은 물체 → 섞어도 OK"
- "50과 200은 차이 큼 → 다른 물체 → 섞지 마!"

### 2.4 무엇이 Guide가 될 수 있나?

**일반적으로:**
1. **원본 grayscale 이미지** ← PA1에서 사용
2. RGB 이미지 (컬러 정보)
3. Depth 이미지 (깊이 정보)
4. 다른 센서 데이터 (적외선, 열화상 등)

**핵심**: Guide는 **경계 정보를 가진 이미지**면 됨

---

## 3. 일반 필터 vs Bilateral Filter

### 3.1 일반 필터 (Box Filter)

**원리**: 주변 픽셀들을 **거리만** 고려하여 평균

```python
# 5×5 Box Filter
중심 픽셀 (x, y)
주변 25개 픽셀 모두 동일한 가중치로 평균
```

**시각적 예시:**
```
이미지:
  10  10  10 | 100 100
  10  10 [X]| 100 100    ← X 위치에서 필터링
  10  10  10 | 100 100

Box Filter (3×3):
  가중치: 모두 1/9
  결과: (10×4 + 100×5) / 9 = 60
       ↑ 10과 100이 섞임!
```

**문제**: 경계를 무시하고 무조건 섞음

### 3.2 Bilateral Filter

**원리**: **거리 + 픽셀 값 차이** 모두 고려

```python
# Bilateral Filter
중심 픽셀 (x, y)
주변 픽셀을:
1. 거리 가까우면 → 가중치 높음
2. 값 비슷하면 → 가중치 높음
3. 둘 다 만족하면 → 가중치 매우 높음
```

**시각적 예시:**
```
이미지:
  10  10  10 | 100 100
  10  10 [X]| 100 100    ← X=10
  10  10  10 | 100 100

Bilateral Filter:
  픽셀 10: 거리 가깝고 + 값 비슷 (10≈10) → 가중치 높음 (0.9)
  픽셀 100: 거리 가깝지만 + 값 다름 (10≠100) → 가중치 낮음 (0.01)

  결과: (10×0.9×4 + 100×0.01×5) / (0.9×4 + 0.01×5) ≈ 10
       ↑ 10만 섞임! 경계 보존!
```

**효과**: 경계를 넘어 섞이지 않음

---

## 4. 공간 가우시안 (Gs)

### 4.1 정의

**공간 가우시안 (Spatial Gaussian)**: **거리**에 따른 가중치

```
중심 픽셀 (x, y)에서
주변 픽셀 (x', y')까지의 "물리적 거리"를 측정
```

### 4.2 수식

```python
Gs(x, y, x', y') = exp( -((x-x')² + (y-y')²) / (2 × sigma_s²) )
                          ↑
                      픽셀 간 거리의 제곱
```

**거리 = √((x-x')² + (y-y')²)**

### 4.3 시각적 예시

```
중심 픽셀 X를 기준으로 5×5 영역:

거리 계산:
  √8  √5  √4  √5  √8
  √5  √2  √1  √2  √5
  √4  √1  [X] √1  √4    ← X는 (0, 0)
  √5  √2  √1  √2  √5
  √8  √5  √4  √5  √8

Gs 가중치 (sigma_s=1.0):
  0.01 0.04 0.14 0.04 0.01
  0.04 0.14 0.61 0.14 0.04
  0.14 0.61 [1.0] 0.61 0.14   ← 중심 가장 높음
  0.04 0.14 0.61 0.14 0.04
  0.01 0.04 0.14 0.04 0.01

특징:
- 중심에 가까울수록 가중치 높음
- 멀수록 가중치 낮음
- 대칭적
```

### 4.4 sigma_s의 영향

```python
sigma_s = 1.0  # 작은 값
→ 가까운 픽셀만 높은 가중치
→ 급격히 감소

sigma_s = 5.0  # 큰 값
→ 멀리 있는 픽셀도 높은 가중치
→ 천천히 감소
```

**비유**: sigma_s = "영향 범위"

---

## 5. 범위 가우시안 (Gr)

### 5.1 정의

**범위 가우시안 (Range Gaussian)**: **픽셀 값 차이**에 따른 가중치

```
중심 픽셀의 값: I(x, y)
주변 픽셀의 값: I(x', y')
차이: |I(x, y) - I(x', y')|
```

### 5.2 수식

```python
Gr(I_center, I_neighbor) = exp( -(I_center - I_neighbor)² / (2 × sigma_r²) )
                                  ↑
                              픽셀 값 차이의 제곱
```

**값 차이 = |I(x, y) - I(x', y')|**

### 5.3 시각적 예시

```
이미지 (grayscale 0-255, 정규화 0-1):
  0.2  0.2  0.2 | 0.8  0.8
  0.2  0.2 [0.2]| 0.8  0.8   ← 중심 픽셀 값=0.2
  0.2  0.2  0.2 | 0.8  0.8

값 차이 계산 (중심 0.2 기준):
  0.0  0.0  0.0 | 0.6  0.6
  0.0  0.0 [0.0]| 0.6  0.6
  0.0  0.0  0.0 | 0.6  0.6

Gr 가중치 (sigma_r=0.1):
  1.0  1.0  1.0 | 0.0001  0.0001
  1.0  1.0 [1.0]| 0.0001  0.0001   ← 비슷한 값만 높은 가중치
  1.0  1.0  1.0 | 0.0001  0.0001

특징:
- 값이 비슷할수록 가중치 높음 (왼쪽 0.2 영역)
- 값이 다를수록 가중치 낮음 (오른쪽 0.8 영역)
- 경계를 넘으면 거의 0!
```

### 5.4 sigma_r의 영향

```python
sigma_r = 0.05  # 작은 값
→ 값이 조금만 달라도 가중치 급감
→ 경계 보존 강함
→ 예: 0.2 vs 0.25 → 가중치 거의 0

sigma_r = 0.5   # 큰 값
→ 값이 많이 달라도 가중치 유지
→ 경계 보존 약함
→ 예: 0.2 vs 0.8 → 가중치 0.3 정도
```

**비유**: sigma_r = "얼마나 비슷해야 섞을까?"

---

## 6. Joint Bilateral Filter

### 6.1 Bilateral Filter와의 차이

**Bilateral Filter:**
```python
# 필터링 대상 이미지 = 픽셀 값 비교 기준 이미지
bilateral_filter(image, image)
                  ↑      ↑
                  같은 이미지
```

**Joint Bilateral Filter:**
```python
# 필터링 대상 이미지 ≠ 픽셀 값 비교 기준 이미지
joint_bilateral_filter(cost_vol, left_image)
                        ↑          ↑
                     필터링 대상  Guide (참고용)
```

### 6.2 핵심 아이디어

```
Cost volume을 부드럽게 하고 싶은데,
어디까지 섞을지를 left_image가 알려줌!
```

**예시:**
```
Left image (guide):
  물체 픽셀: 50
  배경 픽셀: 200

Cost volume (필터링 대상):
  물체 cost: [10, 5, 3, 8, ...]
  배경 cost: [25, 30, 28, 26, ...]

Joint Bilateral Filter:
1. Cost volume의 물체 영역을 부드럽게 할 때
2. Guide (left image)를 보니 값이 50인 영역끼리만 섞어야 함
3. 값이 200인 배경과는 섞지 않음
→ 경계 보존!
```

### 6.3 전체 수식

```python
filtered_cost(x, y) = Σ cost(x', y') × Gs × Gr / W

여기서:
- cost(x', y'): 주변 픽셀의 cost 값 (필터링 대상)
- Gs: exp(-거리² / 2σ_s²)
      거리 = √((x-x')² + (y-y')²)  ← 픽셀 간 물리적 거리

- Gr: exp(-값차이² / 2σ_r²)
      값차이 = |guide(x,y) - guide(x',y')|  ← Guide 이미지의 값 차이!

- W: 정규화 상수 = Σ(Gs × Gr)
```

**핵심**: Gr은 **guide 이미지의 값 차이**를 봄!

---

## 7. PA1에서의 적용

### 7.1 전체 흐름

```
1. Left 이미지 로딩
   left = load_gray("reindeer_left.png")

2. Cost volume 생성
   cost_vol = build_cost_volume(left, right)
   → cost_vol.shape = (H, W, 64)  # 64개 disparity

3. Joint Bilateral Filter로 aggregation
   agg_cost_vol = aggregate_cost_volume_joint_bilateral_numpy(
       cost_vol,    # 필터링 대상: cost
       left,        # Guide: 원본 이미지
       win_radius=3,
       sigma_s=3.0,
       sigma_r=0.1
   )
```

### 7.2 각 Disparity 슬라이스마다 적용

```python
# Cost volume은 3D (H×W×D)
for d in range(64):  # 각 disparity에 대해
    # d번째 슬라이스 (H×W)
    cost_slice = cost_vol[:, :, d]

    # Guide 이미지를 참고하여 필터링
    filtered_slice = joint_bilateral_slice_numpy(
        cost_slice,  # 필터링 대상
        left,        # Guide
        ...
    )

    agg_cost_vol[:, :, d] = filtered_slice
```

### 7.3 구체적 예시

```
순록 이미지 (left, guide):
  순록 몸통: 밝기 100
  배경 하늘: 밝기 200
  경계: 밝기 급변

Cost volume (d=30 슬라이스):
  순록 위치 cost: 5
  배경 위치 cost: 50

경계 픽셀 (150, 200)에서 필터링:
1. 주변 7×7 영역 확인
2. 왼쪽 픽셀들 (순록, 밝기≈100): Gr 높음 → cost=5와 섞임
3. 오른쪽 픽셀들 (하늘, 밝기≈200): Gr 낮음 → cost=50와 안 섞임
→ 결과: 순록의 cost만 반영 → 경계 선명!
```

---

## 8. 실전 예시

### 8.1 Python 코드로 이해하기

```python
def joint_bilateral_slice_numpy(src, guide, win_radius=3, sigma_s=3.0, sigma_r=0.1):
    H, W = src.shape
    out = np.zeros_like(src)

    # 1. 공간 가우시안 미리 계산 (거리 기반)
    ksize = 2 * win_radius + 1  # 7
    ys, xs = np.mgrid[-3:4, -3:4]  # -3, -2, -1, 0, 1, 2, 3

    # 거리² = x² + y²
    dist_sq = xs**2 + ys**2

    # Gs = exp(-거리² / 2σ_s²)
    Gs = np.exp(-dist_sq / (2 * sigma_s**2))

    # 2. 각 픽셀마다 필터링
    for y in range(H):
        for x in range(W):
            # 2.1 중심 픽셀의 guide 값
            g_center = guide[y, x]  # 예: 0.4 (정규화된 밝기)

            # 2.2 주변 7×7 영역
            src_patch = src[y:y+7, x:x+7]      # Cost 값들
            guide_patch = guide[y:y+7, x:x+7]  # Guide 값들

            # 2.3 범위 가우시안 계산 (guide 값 차이 기반)
            # 값차이² = (g_center - guide_patch)²
            value_diff_sq = (guide_patch - g_center)**2

            # Gr = exp(-값차이² / 2σ_r²)
            Gr = np.exp(-value_diff_sq / (2 * sigma_r**2))

            # 2.4 최종 가중치 = Gs × Gr
            weight = Gs * Gr

            # 2.5 가중 평균
            numerator = (src_patch * weight).sum()    # 가중치 × cost
            denominator = weight.sum() + 1e-8         # 정규화

            out[y, x] = numerator / denominator

    return out
```

### 8.2 단계별 예시

**입력:**
```
Guide 이미지 (정규화 0-1):
  0.2  0.2  0.2 | 0.8  0.8  0.8
  0.2  0.2 [X] | 0.8  0.8  0.8   ← X = (3, 2)
  0.2  0.2  0.2 | 0.8  0.8  0.8

Cost 값:
  10   10   10  | 50   50   50
  10   10  [10] | 50   50   50   ← 필터링할 픽셀
  10   10   10  | 50   50   50
```

**필터링 과정 (X = (3, 2), 3×3 window):**

```python
# Step 1: 중심 픽셀 guide 값
g_center = 0.2

# Step 2: 공간 가우시안 (거리 기반)
Gs = [[0.14, 0.61, 0.14],   # 미리 계산됨
      [0.61, 1.00, 0.61],
      [0.14, 0.61, 0.14]]

# Step 3: 주변 guide 값
guide_patch = [[0.2, 0.2, 0.8],
               [0.2, 0.2, 0.8],
               [0.2, 0.2, 0.8]]

# Step 4: 값 차이 계산
value_diff = [[0.0, 0.0, 0.6],    # |0.2 - guide_patch|
              [0.0, 0.0, 0.6],
              [0.0, 0.0, 0.6]]

# Step 5: 범위 가우시안 (sigma_r=0.1)
Gr = [[1.0, 1.0, 0.0001],   # exp(-0.6² / 2×0.1²) ≈ 0
      [1.0, 1.0, 0.0001],
      [1.0, 1.0, 0.0001]]

# Step 6: 최종 가중치 = Gs × Gr
weight = [[0.14, 0.61, 0.0],   # 오른쪽(0.8)은 거의 0!
          [0.61, 1.00, 0.0],
          [0.14, 0.61, 0.0]]

# Step 7: Cost 값
cost_patch = [[10, 10, 50],
              [10, 10, 50],
              [10, 10, 50]]

# Step 8: 가중 평균
numerator = 10×0.14 + 10×0.61 + 50×0.0 + ... = 10 × (sum of weights)
denominator = 0.14 + 0.61 + 0.0 + ... = 3.0

result = 10 × 3.0 / 3.0 = 10

→ Cost 50은 거의 기여하지 않음!
→ Cost 10만 섞임!
→ 경계 보존 성공!
```

### 8.3 Box Filter와 비교

**같은 상황에서 Box Filter:**
```python
# 모든 픽셀 동일 가중치
weight = [[1/9, 1/9, 1/9],
          [1/9, 1/9, 1/9],
          [1/9, 1/9, 1/9]]

result = (10×5 + 50×4) / 9 = 27.8
         ↑ 10과 50이 섞임! 경계 흐려짐!
```

**Joint Bilateral Filter:**
```python
# Guide를 참고한 가중치
weight = [[high, high, ~0],
          [high, high, ~0],
          [high, high, ~0]]

result = 10
         ↑ 10만 섞임! 경계 보존!
```

---

## 9. 왜 경계에서 Disparity가 섞이지 않나?

### 9.1 물리적 의미

```
실제 3D 장면:
  순록 (가까움, d=50) | 배경 (멀리, d=10)
  ━━━━━━━━━━━━━━━━━┃━━━━━━━━━━━━━━━━
                   경계
```

### 9.2 Box Filter의 문제

```
경계 픽셀에서:
- 왼쪽 픽셀들의 cost (d=50일 때 낮음) ─┐
- 오른쪽 픽셀들의 cost (d=10일 때 낮음) ─┤ 둘 다 섞임!
                                        ↓
                             중간 값 (d=30)이 선택됨 ❌
```

### 9.3 Joint Bilateral Filter의 해결

```
경계 픽셀에서:
1. Guide 이미지를 보니 왼쪽과 오른쪽의 밝기가 다름
2. Gr이 경계를 넘으면 0에 가까움
3. 왼쪽 픽셀들의 cost만 섞임
4. 올바른 disparity 선택 ✅

결과:
  순록 영역: d=50 유지
  배경 영역: d=10 유지
  경계: 선명하게 구분!
```

### 9.4 핵심 원리

**Guide 이미지의 역할:**
```
물체 경계 = 밝기 급변
→ Gr(값차이) ≈ 0
→ 경계 너머 cost와 섞이지 않음
→ 각 물체의 disparity 보존
```

---

## 10. 요약

### 10.1 핵심 개념

| 개념 | 의미 | 측정 대상 |
|------|------|----------|
| **Guide 이미지** | 경계 정보를 알려주는 참고 이미지 | Left 원본 이미지 |
| **공간 가우시안 (Gs)** | 거리 기반 가중치 | 픽셀 간 물리적 거리 |
| **범위 가우시안 (Gr)** | 값 차이 기반 가중치 | **Guide 이미지의 픽셀 값 차이** |
| **가중치** | Gs × Gr | 거리 가깝고 + 값 비슷하면 높음 |

### 10.2 작동 원리

```
1. Cost volume을 부드럽게 하고 싶음
2. Guide (left 이미지)를 참고
3. Guide에서 값이 비슷한 픽셀끼리만 섞음
4. 경계를 넘으면 값이 다르므로 안 섞임
5. 결과: 경계 보존된 부드러운 cost volume
```

### 10.3 PA1에서의 효과

**Box Filter:**
- 빠름 ⚡
- 경계 흐려짐 😢

**Joint Bilateral Filter:**
- 느림 🐢
- 경계 선명 ✨
- 물체와 배경의 disparity가 섞이지 않음
- 더 정확한 깊이 추정

---

## 11. 마지막 질문 답변

### Q1: Guide 이미지란?
**A**: 필터링할 때 참고하는 이미지. 물체 경계 정보를 알려줌.

### Q2: 무엇이 guide가 될 수 있나?
**A**: 경계 정보를 가진 아무 이미지. PA1에서는 left 원본 이미지.

### Q3: Guide로 어떻게 depth를 구하나?
**A**: Guide의 경계 정보로 cost를 섞을지 말지 결정 → 정확한 disparity 선택 → 깊이 계산.

### Q4: 공간/범위 가우시안은?
**A**:
- 공간: 픽셀 간 거리로 가중치 계산
- 범위: **Guide 이미지의 값 차이**로 가중치 계산

### Q5: Gs, Gr은 무엇과의 거리/차이?
**A**:
- Gs: 중심 픽셀 (x, y)와 주변 픽셀 (x', y')의 **물리적 거리**
- Gr: 중심 픽셀의 **guide 값**과 주변 픽셀의 **guide 값** 차이

### Q6: 왜 경계에서 섞이지 않나?
**A**: Guide에서 경계 = 값 급변 → Gr ≈ 0 → 가중치 거의 0 → 안 섞임!

---

**이제 Joint Bilateral Filter를 완전히 이해하셨나요?** 🎯
