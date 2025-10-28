# Weighted Median Filter 완전 이해 가이드

## 목차
1. [문제 상황: 왜 필요한가?](#1-문제-상황-왜-필요한가)
2. [Median Filter 기초](#2-median-filter-기초)
3. [Weighted Median이란?](#3-weighted-median이란)
4. [Guide 이미지의 역할](#4-guide-이미지의-역할)
5. [가중치 계산 방법](#5-가중치-계산-방법)
6. [Weighted Median 계산 알고리즘](#6-weighted-median-계산-알고리즘)
7. [PA1에서의 적용](#7-pa1에서의-적용)
8. [실전 예시](#8-실전-예시)
9. [왜 Outlier 제거에 효과적인가?](#9-왜-outlier-제거에-효과적인가)

---

## 1. 문제 상황: 왜 필요한가?

### 1.1 Disparity Map의 문제점

Disparity selection (winner-takes-all) 후에도 여전히 **노이즈**와 **이상치(outlier)**가 존재합니다:

```
이상적인 disparity map:
  물체: 50 50 50 50 50
  배경: 10 10 10 10 10

실제 disparity map:
  물체: 50 50 [3] 50 50    ← 중간에 outlier!
  배경: 10 [45] 10 10 10   ← 중간에 outlier!
```

**원인:**
- Textureless 영역 (텍스처 없는 벽, 하늘)
- Occlusion (가려진 영역)
- 반복 패턴 (repetitive texture)
- 노이즈 (센서 노이즈, 조명 변화)

### 1.2 기존 필터의 한계

**Mean Filter (평균):**
```python
값: [50, 50, 3, 50, 50]
평균: (50+50+3+50+50) / 5 = 40.6
      ↑ Outlier 3이 평균을 크게 왜곡!
```

**Gaussian Filter:**
```python
# 가중 평균이지만 여전히 outlier 영향
가중 평균: 50×0.2 + 50×0.2 + 3×0.2 + 50×0.2 + 50×0.2 = 40.6
```

**문제**: Outlier에 **민감**

### 1.3 해결책: Median Filter

```python
값: [50, 50, 3, 50, 50]
정렬: [3, 50, 50, 50, 50]
중간값:       ↑ 50
      ↑ Outlier 무시!
```

**장점**: Outlier에 **강건(robust)**

하지만 단순 median은 **경계를 무시**합니다. → **Weighted Median** 필요!

---

## 2. Median Filter 기초

### 2.1 Median이란?

**정의**: 값들을 정렬했을 때 **중간에 위치한 값**

```
홀수 개: [1, 3, 5, 7, 9]
        정렬:    [1, 3, 5, 7, 9]
        Median:       ↑ 5

짝수 개: [1, 3, 5, 7]
        정렬: [1, 3, 5, 7]
        Median:    ↑↑ (3+5)/2 = 4
```

### 2.2 Median Filter 동작

**3×3 Median Filter:**
```
이미지:
  10  10  10
  10 [X] 10    ← X 위치 필터링
  10  10 100

주변 9개 값: [10, 10, 10, 10, X, 10, 10, 10, 100]
정렬: [10, 10, 10, 10, 10, 10, 10, X, 100]
Median:                      ↑ 10

결과: 10 (outlier 100 무시!)
```

### 2.3 Median vs Mean

**예시: Salt-and-pepper noise**
```
원본:  10  10  10  10  10
노이즈: 10 255  10 255  10

Mean Filter:
(10+255+10+255+10) / 5 = 108  ← 엉망

Median Filter:
정렬: [10, 10, 10, 255, 255]
Median:       ↑ 10  ← 정확!
```

### 2.4 Median Filter의 한계

```
물체 A (d=50) | 배경 B (d=10)
━━━━━━━━━━━━┃━━━━━━━━━━━━
           경계

경계 픽셀에서 3×3 median:
값: [50, 50, 50, 50, X, 10, 10, 10, 10]
정렬: [10, 10, 10, 10, 50, 50, 50, 50, X]
Median:                ↑ 50 또는 10 (불안정)

문제: 경계를 무시하고 모든 값 섞음
```

**해결책**: 경계 정보를 고려 → **Weighted Median**

---

## 3. Weighted Median이란?

### 3.1 정의

**Weighted Median**: 각 값에 **가중치**를 부여하여 계산한 중간값

```
일반 Median: 모든 값이 동등
Weighted Median: 중요한 값에 더 큰 영향
```

### 3.2 개념

**예시:**
```
값:      [10, 20, 30]
가중치:  [1,  1,  1]   ← 모두 동등

확장:    [10, 20, 30]
       = [10 ×1, 20 ×1, 30 ×1]
       = [10, 20, 30]
Median: 20
```

**가중치 부여:**
```
값:      [10, 20, 30]
가중치:  [0.1, 0.7, 0.2]  ← 20에 높은 가중치

개념적으로:
10이 10% 중요
20이 70% 중요  ← 가장 중요!
30이 20% 중요

Weighted Median: 20
(가중치가 높은 20이 선택됨)
```

### 3.3 Weighted Median 계산 방법

**알고리즘:**
1. 값들을 정렬
2. 가중치의 **누적합(cumulative sum)** 계산
3. 누적합이 **전체의 50%**가 되는 지점의 값 선택

**예시:**
```
값:          [10, 20, 30, 40]
가중치:      [0.1, 0.3, 0.4, 0.2]

Step 1: 값으로 정렬 (이미 정렬됨)
Step 2: 누적 가중치
  10: 0.1        (10%)
  20: 0.1+0.3=0.4 (40%)
  30: 0.4+0.4=0.8 (80%)  ← 50% 넘는 첫 지점
  40: 0.8+0.2=1.0 (100%)

Step 3: 50% 지점 = 0.5
  0.5는 0.4와 0.8 사이
  → Weighted Median = 30
```

---

## 4. Guide 이미지의 역할

### 4.1 Weighted Median Filter에서의 Guide

**Joint Bilateral Filter와 같은 원리:**
- Filtering 대상: Disparity map
- Guide: 원본 left 이미지
- Guide로 가중치 계산

```python
weighted_median_filter(
    disparity,    # 필터링 대상
    left_image    # Guide (경계 정보)
)
```

### 4.2 Guide가 가중치를 결정

```
Guide 이미지:
  0.2  0.2  0.2 | 0.8  0.8  0.8
  0.2  0.2 [X] | 0.8  0.8  0.8   ← X=0.2
  0.2  0.2  0.2 | 0.8  0.8  0.8
  물체 A         | 배경 B
               ↑ 경계

가중치 (X=0.2 기준):
- 왼쪽 픽셀 (0.2): guide 값 비슷 → 가중치 높음
- 오른쪽 픽셀 (0.8): guide 값 다름 → 가중치 낮음
```

**효과**: 같은 물체 내 값들이 median 계산에 더 큰 영향

---

## 5. 가중치 계산 방법

### 5.1 Bilateral 가중치 재사용

**Weighted Median도 Bilateral 방식 사용:**
```python
weight = Gs × Gr

Gs: 공간 가우시안 (거리 기반)
Gr: 범위 가우시안 (guide 값 차이 기반)
```

**Joint Bilateral Filter와 동일!**

### 5.2 공간 가우시안 (Gs)

```python
distance = √((x-x')² + (y-y')²)
Gs = exp(-distance² / (2 × sigma_s²))
```

**예시 (7×7 window, sigma_s=3.0):**
```
중심 픽셀 기준 거리:
  √8  √5  √2  √1   0  √1  √2
  √5  √2  √1   0  √1  √2  √5
  √2  √1   0  √1  √2  √5  √8
  √1   0  √1  √2  √5  √8  √13
   0  √1  √2  √5  √8  √13 √18
  ...

Gs (가중치):
  0.14 0.24 0.61 0.78 1.0 0.78 0.61
  0.24 0.61 0.78 1.0 0.78 0.61 0.24
  ...
```

### 5.3 범위 가우시안 (Gr)

```python
g_center = guide[y, x]
g_neighbor = guide[y', x']
value_diff = |g_center - g_neighbor|
Gr = exp(-value_diff² / (2 × sigma_r²))
```

**예시 (sigma_r=0.08):**
```
Guide 값:
  0.2  0.2  0.2 | 0.8  0.8
  0.2  0.2 [X] | 0.8  0.8   ← X=0.2
  0.2  0.2  0.2 | 0.8  0.8

값 차이:
  0.0  0.0  0.0 | 0.6  0.6
  0.0  0.0 [0.0]| 0.6  0.6
  0.0  0.0  0.0 | 0.6  0.6

Gr (sigma_r=0.08):
  1.0  1.0  1.0 | ~0.0  ~0.0
  1.0  1.0 [1.0]| ~0.0  ~0.0
  1.0  1.0  1.0 | ~0.0  ~0.0
```

### 5.4 최종 가중치

```python
weight = Gs × Gr

경계 내 (왼쪽, guide=0.2):
  Gs: 높음, Gr: 높음 → weight: 높음 ✅

경계 넘음 (오른쪽, guide=0.8):
  Gs: 높음, Gr: ~0 → weight: ~0 ❌
```

---

## 6. Weighted Median 계산 알고리즘

### 6.1 전체 알고리즘

```python
def weighted_median(values, weights):
    """
    values: 주변 픽셀의 disparity 값들
    weights: 각 값의 가중치
    """
    # Step 1: 값으로 정렬
    sorted_indices = np.argsort(values)
    sorted_values = values[sorted_indices]
    sorted_weights = weights[sorted_indices]

    # Step 2: 가중치 누적합
    cumsum = np.cumsum(sorted_weights)

    # Step 3: 전체 가중치의 50% 지점
    total_weight = cumsum[-1]
    half_weight = total_weight * 0.5

    # Step 4: 50% 지점의 값 찾기
    idx = np.searchsorted(cumsum, half_weight)
    return sorted_values[idx]
```

### 6.2 단계별 예시

**입력:**
```
Disparity 값: [50, 50, 3, 50, 50]  (중간에 outlier)
가중치:       [0.2, 0.3, 0.05, 0.3, 0.15]
```

**Step 1: 정렬**
```
값:    [3, 50, 50, 50, 50]
가중치: [0.05, 0.2, 0.3, 0.3, 0.15]
```

**Step 2: 누적 가중치**
```
값:         [3,    50,   50,   50,   50]
가중치:     [0.05, 0.2,  0.3,  0.3,  0.15]
누적 가중치: [0.05, 0.25, 0.55, 0.85, 1.0]
            5%    25%   55%   85%   100%
```

**Step 3: 50% 지점**
```
half_weight = 1.0 × 0.5 = 0.5

누적 가중치:
  0.05 (5%)   ← 50% 미만
  0.25 (25%)  ← 50% 미만
  0.55 (55%)  ← 50% 넘는 첫 지점! ✅
  0.85 (85%)
  1.0  (100%)
```

**Step 4: 결과**
```
idx = 2 (0.55가 있는 인덱스)
Weighted Median = sorted_values[2] = 50 ✅

outlier 3은 가중치가 낮아서 무시됨!
```

### 6.3 일반 Median과 비교

**일반 Median:**
```
값: [3, 50, 50, 50, 50]
Median:     ↑ 50 (3번째 값)
```

**Weighted Median (가중치 없이):**
```
값:       [3,  50, 50, 50, 50]
가중치:   [0.2, 0.2, 0.2, 0.2, 0.2]  ← 모두 동등
누적:     [0.2, 0.4, 0.6, 0.8, 1.0]
50% 지점:           ↑ 0.6 (3번째)
Weighted Median: 50
```

**결과**: 가중치가 동등하면 일반 median과 같음

---

## 7. PA1에서의 적용

### 7.1 전체 흐름

```
1. Disparity selection 완료
   disp = select_disparity(agg_cost_vol)
   → disp.shape = (H, W)

2. Weighted Median Filter 적용
   disp_filtered = weighted_median_disparity_numpy(
       disp,        # 필터링 대상
       left,        # Guide
       win_radius=3,
       sigma_s=3.0,
       sigma_r=0.08
   )

3. 결과: 부드럽고 outlier 없는 disparity map
```

### 7.2 각 픽셀마다 적용

```python
for y in range(H):
    for x in range(W):
        # 1. 주변 7×7 영역의 disparity 값들
        disp_patch = disp[y:y+7, x:x+7]  # 49개 값

        # 2. Guide 이미지 참고하여 가중치 계산
        g_center = guide[y, x]
        guide_patch = guide[y:y+7, x:x+7]

        # 3. Bilateral 가중치
        Gs = spatial_gaussian(...)
        Gr = range_gaussian(guide_patch, g_center, ...)
        weights = Gs * Gr  # (7×7)

        # 4. Weighted Median 계산
        wm = weighted_median(disp_patch, weights)

        # 5. 결과 저장
        disp_filtered[y, x] = wm
```

### 7.3 구체적 예시

```
Disparity (경계 픽셀 주변 3×3):
  50  50  50
  50 [X] 10
  10  10  10

Guide (정규화):
  0.2  0.2  0.2
  0.2 [X] 0.8
  0.8  0.8  0.8

X = (1, 1), guide=0.2

가중치 계산:
  Gs × Gr:
    높음 높음 높음
    높음 최대 낮음
    낮음 낮음 낮음

Disparity + 가중치:
  값:    [50, 50, 50, 50, X, 10, 10, 10, 10]
  가중치: [0.8, 0.8, 0.8, 0.8, 1.0, 0.01, 0.01, 0.01, 0.01]

정렬 후:
  값:    [10, 10, 10, 10, 50, 50, 50, 50, X]
  가중치: [0.01, 0.01, 0.01, 0.01, 0.8, 0.8, 0.8, 0.8, 1.0]

누적 가중치:
  [0.01, 0.02, 0.03, 0.04, 0.84, 1.64, 2.44, 3.24, 4.24]

전체: 4.24
50%: 2.12
→ 누적 2.44가 첫 번째로 2.12 넘음
→ Weighted Median = 50 ✅

물체 A의 disparity 유지!
```

---

## 8. 실전 예시

### 8.1 Python 코드

```python
def weighted_median_disparity_numpy(disp, guide_gray,
                                     win_radius=3, sigma_s=3.0, sigma_r=0.1):
    disp = disp.astype(np.float32)
    guide = guide_gray.astype(np.float32) / 255.0  # 0-1 정규화
    H, W = disp.shape
    out = np.zeros_like(disp)

    k = 2*win_radius + 1  # 7

    # 1. 공간 가우시안 미리 계산
    ys, xs = np.mgrid[-win_radius:win_radius+1, -win_radius:win_radius+1]
    Gs = np.exp(-(xs**2 + ys**2) / (2 * sigma_s**2))

    # 2. Padding
    pad = win_radius
    d_p = np.pad(disp, pad, mode='reflect')
    g_p = np.pad(guide, pad, mode='reflect')

    # 3. 각 픽셀마다
    for y in range(H):
        for x in range(W):
            # 3.1 중심 guide 값
            g0 = g_p[y+pad, x+pad]

            # 3.2 주변 패치
            d_patch = d_p[y:y+k, x:x+k]  # Disparity
            g_patch = g_p[y:y+k, x:x+k]  # Guide

            # 3.3 범위 가우시안
            Gr = np.exp(-((g_patch - g0)**2) / (2 * sigma_r**2))

            # 3.4 최종 가중치
            Wgt = (Gs * Gr).reshape(-1)  # 1D로 flatten
            Vals = d_patch.reshape(-1)

            # 3.5 Weighted Median 계산
            order = np.argsort(Vals)       # 정렬
            w_sorted = Wgt[order]          # 가중치도 같은 순서
            v_sorted = Vals[order]         # 정렬된 값들

            csum = np.cumsum(w_sorted)     # 누적합
            half = csum[-1] * 0.5          # 50% 지점
            idx = np.searchsorted(csum, half)  # 50% 지점 인덱스

            # 3.6 결과
            out[y, x] = v_sorted[min(idx, v_sorted.size-1)]

    return out
```

### 8.2 단계별 디버깅

**테스트 데이터:**
```python
# 간단한 3×3 예시
disp = np.array([
    [10, 10, 10],
    [10, 50, 10],  # 중심이 outlier
    [10, 10, 10]
], dtype=np.float32)

guide = np.array([
    [0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1]
], dtype=np.float32)  # 모두 같은 영역
```

**실행:**
```python
result = weighted_median_disparity_numpy(disp, guide*255,
                                          win_radius=1,
                                          sigma_s=1.0,
                                          sigma_r=0.1)

print(result[1, 1])  # 중심 픽셀
# 기대: 10 (outlier 50 제거됨)
```

**내부 동작:**
```
중심 픽셀 (1, 1):

Step 1: 주변 값들
  [10, 10, 10, 10, 50, 10, 10, 10, 10]

Step 2: 가중치 (guide 모두 비슷하므로 Gr≈1)
  Gs만 적용: [0.14, 0.61, 0.14, 0.61, 1.0, 0.61, 0.14, 0.61, 0.14]

Step 3: 정렬
  값:    [10, 10, 10, 10, 10, 10, 10, 10, 50]
  가중치: [0.14, 0.61, 0.14, 0.61, 0.61, 0.14, 0.61, 0.14, 1.0]

Step 4: 누적 가중치
  [0.14, 0.75, 0.89, 1.50, 2.11, 2.25, 2.86, 3.00, 4.00]

Step 5: 50% = 2.0
  → idx = 4 (누적 2.11)
  → Weighted Median = 10 ✅

Outlier 50은 가중치가 있어도 다수의 10에 밀림!
```

---

## 9. 왜 Outlier 제거에 효과적인가?

### 9.1 Median의 본질적 강건성

**Mean vs Median:**
```
정상 값: [10, 10, 10, 10, 10]
Outlier 추가: [10, 10, 10, 10, 10, 100]

Mean:
  (10×5 + 100) / 6 = 25  ← 크게 왜곡

Median:
  정렬: [10, 10, 10, 10, 10, 100]
  중간:          ↑↑ (10+10)/2 = 10  ← 정확!
```

**핵심**: Median은 **순서**만 보므로 극단값 영향 최소

### 9.2 Weighted Median의 추가 이점

**일반 Median 문제:**
```
경계에서:
  물체: [50, 50, 50, 50]
  배경: [10, 10, 10, 10, 10]

정렬: [10, 10, 10, 10, 10, 50, 50, 50, 50]
Median:                ↑ 10 (배경 쪽으로 치우침)
```

**Weighted Median 해결:**
```
경계 픽셀이 물체 쪽이라면:
  물체 값들: 가중치 높음
  배경 값들: 가중치 낮음 (guide 다름)

값:      [10, 10, 10, 10, 10, 50, 50, 50, 50]
가중치:  [0.01, 0.01, 0.01, 0.01, 0.01, 0.8, 0.8, 0.8, 0.8]

누적 가중치:
  [0.01, 0.02, 0.03, 0.04, 0.05, 0.85, 1.65, 2.45, 3.25]

50% = 1.625
→ 누적 1.65가 첫 50% 넘음
→ Weighted Median = 50 ✅

물체의 disparity 보존!
```

### 9.3 경계 보존 + Outlier 제거

**Weighted Median의 이중 효과:**

1. **경계 보존** (Guide 활용)
   - 같은 물체 내 값들만 median 계산에 참여
   - 다른 물체 값은 가중치 낮아서 영향 최소

2. **Outlier 제거** (Median 본질)
   - 극단값은 median에 영향 없음
   - 다수의 정상 값이 median 결정

**최고의 조합!**

### 9.4 실제 예시

**상황: 텍스처 없는 벽에 노이즈**
```
원본 disparity (벽, 이상적으로는 모두 30):
  30  30  30  30  30
  30  30  [5] 30  30  ← Outlier!
  30  30  30  30  30
  30  30  30  [60] 30  ← Outlier!
  30  30  30  30  30
```

**Box Filter (mean):**
```
중심 픽셀 3×3 평균:
  (30×8 + 5) / 9 = 27.2  ← 왜곡
```

**일반 Median Filter:**
```
중심 픽셀 3×3 median:
  [5, 30, 30, 30, 30, 30, 30, 30, 30]
  Median:     ↑ 30  ← 정확! ✅
```

**Weighted Median Filter:**
```
Guide가 모두 비슷 (벽) → 가중치 비슷
동작: 일반 median과 유사
결과: 30 ✅

추가 이점: 벽 경계에서도 보존
```

**상황: 경계 근처 outlier**
```
물체 (50) | 배경 (10)
━━━━━━━┃━━━━━━━

경계 픽셀 주변:
  50  50  50
  50 [3] 10  ← Outlier 3
  10  10  10
```

**일반 Median:**
```
값: [3, 10, 10, 10, 10, 50, 50, 50, 50]
Median:                ↑ 10 (잘못됨)
```

**Weighted Median (물체 쪽 픽셀):**
```
Guide 참고:
  물체 값들: 가중치 높음
  배경 값들: 가중치 낮음

값:     [3,    10,   10,   10,   10,   50,  50,  50,  50]
가중치: [1.0,  0.01, 0.01, 0.01, 0.01, 0.8, 0.8, 0.8, 0.8]

Weighted Median: 50 ✅

Outlier 제거 + 경계 보존!
```

---

## 10. 요약

### 10.1 핵심 개념

| 개념 | 의미 |
|------|------|
| **Median** | 정렬 후 중간 값 |
| **Weighted Median** | 가중치 고려한 중간 값 (누적 50% 지점) |
| **Guide 이미지** | 가중치 계산의 기준 (경계 정보) |
| **가중치** | Gs × Gr (거리 + guide 값 차이) |
| **효과** | Outlier 제거 + 경계 보존 |

### 10.2 작동 원리

```
1. Disparity map에 노이즈/outlier 존재
2. Guide (left 이미지)를 참고하여 가중치 계산
3. Guide에서 비슷한 값끼리 높은 가중치
4. Weighted median으로 중심 값 결정
5. Outlier는 가중치 낮거나 median 원리로 무시
6. 결과: 부드럽고 경계 보존된 disparity map
```

### 10.3 PA1에서의 효과

**Box Filter:**
- 빠름 ⚡
- 경계 흐려짐 😢
- Outlier에 민감 😢

**Joint Bilateral Filter (TODO6):**
- 느림 🐢
- 경계 선명 ✨
- Outlier에는 여전히 영향 😐

**Weighted Median Filter (TODO7):**
- 매우 느림 🐌
- 경계 선명 ✨
- Outlier 제거 ✨✨
- **최고 품질!**

### 10.4 사용 시나리오

**기본 과제:**
- Box Filter로 충분

**고급 점수:**
- JBF + WMF 조합
- JBF로 경계 보존
- WMF로 outlier 제거 및 추가 smoothing

### 10.5 파라미터 가이드

```python
# 경계 강하게 보존
sigma_r = 0.05  # 작은 값

# Outlier 강하게 제거
win_radius = 5  # 큰 window (더 많은 값 참고)

# 추천 조합 (PA1)
win_radius=3, sigma_s=3.0, sigma_r=0.08
```

---

## 11. 마지막 질문 답변

### Q1: Weighted Median이란?
**A**: 각 값에 가중치를 부여하여 계산한 중간값. 가중치 누적합이 50%가 되는 지점의 값.

### Q2: 왜 Outlier 제거에 효과적?
**A**: Median은 극단값에 강건 + Weighted는 경계 고려 → 이중 효과!

### Q3: Guide는 어떻게 사용?
**A**: Guide 값이 비슷한 픽셀에 높은 가중치 → 같은 물체 내 값들이 median 결정.

### Q4: JBF와의 차이는?
**A**:
- JBF: 가중 **평균** (mean) → 부드럽게
- WMF: 가중 **중간값** (median) → outlier 제거

### Q5: 둘 다 사용하는 이유?
**A**:
- JBF: Cost aggregation 단계에서 경계 보존
- WMF: Disparity refinement 단계에서 outlier 제거
- 상호 보완적!

---

**이제 Weighted Median Filter를 완전히 이해하셨나요?** 🎯
