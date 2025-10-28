# Bilateral Filter vs Joint Bilateral Filter: 핵심 차이

## 핵심을 먼저!

**가장 중요한 차이 단 한 줄:**
```
Bilateral Filter:     필터링할 이미지 = Gr 계산에 사용하는 이미지 (같음)
Joint Bilateral Filter: 필터링할 이미지 ≠ Gr 계산에 사용하는 이미지 (다름)
```

---

## 1. Bilateral Filter 완전 분해

### 1.1 무엇을 하는가?

**한 마디로:** 이미지를 부드럽게 하되, **경계는 보존**

```
일반 Blur (Gaussian):
  [물체 | 배경] → [물체와배경섞임] ← 경계 흐려짐 ❌

Bilateral Filter:
  [물체 | 배경] → [물체 | 배경] ← 경계 선명 유지 ✅
```

### 1.2 어떻게 작동하나?

**두 가지 가우시안을 곱해서 사용:**

#### Gs (Spatial Gaussian): 거리 기반
```python
# 중심 픽셀에서 주변 픽셀까지의 거리
distance = √((x-x')² + (y-y')²)
Gs = exp(-distance² / (2×σ_s²))

예시 (3×3 window):
  0.14  0.61  0.14
  0.61  1.00  0.61    ← 중심이 가장 높음
  0.14  0.61  0.14
```

#### Gr (Range Gaussian): 픽셀 값 차이 기반
```python
# 중심 픽셀과 주변 픽셀의 값 차이
value_diff = |image[y,x] - image[y',x']|
Gr = exp(-value_diff² / (2×σ_r²))

예시:
중심 픽셀 값: 100
주변 픽셀 값: 105 → 차이 5  → Gr = 0.9 (높음)
주변 픽셀 값: 200 → 차이 100 → Gr = 0.0 (거의 0)
```

#### 최종 가중치 = Gs × Gr
```python
weight[y', x'] = Gs[y', x'] × Gr[y', x']

# 두 조건 모두 만족해야 높은 가중치:
# 1. 거리 가까워야 함 (Gs 높음)
# 2. 픽셀 값 비슷해야 함 (Gr 높음)
```

### 1.3 구체적 예시

**원본 이미지 (grayscale 0-255):**
```
  100  100  100 | 200  200  200
  100  100 [X] | 200  200  200   ← X=100을 필터링
  100  100  100 | 200  200  200
  물체          | 배경
              ↑ 경계
```

**중심 픽셀 X=100에서 3×3 bilateral filtering:**

**Step 1: Gs 계산 (거리)**
```
중심 (1,1) 기준 거리:
  √2  √1   √2
  √1   0   √1
  √2  √1   √2

Gs (σ_s=1.0):
  0.14  0.61  0.14
  0.61  1.00  0.61
  0.14  0.61  0.14
```

**Step 2: Gr 계산 (픽셀 값 차이)**
```
주변 픽셀 값:
  100  100  200
  100 [100] 200
  100  100  200

중심 값 100과의 차이:
  0    0   100
  0   [0]  100
  0    0   100

Gr (σ_r=30):
  1.0  1.0  0.0    ← 값 비슷하면 1, 다르면 0
  1.0  1.0  0.0
  1.0  1.0  0.0
```

**Step 3: 최종 가중치 = Gs × Gr**
```
  0.14  0.61  0.0    ← 오른쪽(배경)은 0!
  0.61  1.00  0.0
  0.14  0.61  0.0
```

**Step 4: 가중 평균**
```
분자 = 100×0.14 + 100×0.61 + 200×0.0 + ... + 100×0.61
     = 100 × (0.14 + 0.61 + 0.61 + 1.0 + 0.61 + 0.14 + 0.61)
     = 100 × 3.72
     = 372

분모 = 0.14 + 0.61 + 0.0 + 0.61 + 1.0 + 0.0 + 0.14 + 0.61 + 0.0
     = 3.72

결과 = 372 / 3.72 = 100 ✅

배경(200) 값은 섞이지 않음!
```

### 1.4 핵심 포인트

**Bilateral Filter의 Gr은 필터링 대상 이미지 자신의 픽셀 값 차이를 봄:**
```python
# Bilateral Filter
image = [100, 100, 100, 200, 200, 200]
filtered_image = bilateral_filter(image)

# Gr 계산 시:
Gr = exp(-(image[중심] - image[주변])² / (2×σ_r²))
           ↑           ↑
        같은 이미지!
```

---

## 2. Joint Bilateral Filter의 등장

### 2.1 왜 필요한가?

**문제 상황:**
```
필터링하고 싶은 것: Cost volume (disparity별 매칭 비용)
경계 정보가 있는 곳: 원본 이미지 (left image)

Cost volume에는 경계가 보이지 않음!
→ 어디까지 섞어야 할지 모름
→ 원본 이미지를 참고해야 함
```

### 2.2 Joint Bilateral Filter란?

**정의:** 다른 이미지(guide)를 참고하여 Gr을 계산하는 bilateral filter

```
일반 Bilateral:  필터링 대상 자신을 보고 Gr 계산
Joint Bilateral: 다른 이미지(guide)를 보고 Gr 계산
```

### 2.3 구체적 비교

#### Bilateral Filter (일반)
```python
def bilateral_filter(image):
    filtered = zeros_like(image)

    for 각 픽셀 (x, y):
        center_value = image[y, x]

        for 주변 픽셀 (x', y'):
            # Gs: 거리
            Gs = exp(-distance² / (2×σ_s²))

            # Gr: 같은 이미지의 값 차이 ★
            neighbor_value = image[y', x']
            Gr = exp(-(center_value - neighbor_value)² / (2×σ_r²))

            weight = Gs × Gr
            filtered[y, x] += image[y', x'] × weight

    return filtered / normalize
```

#### Joint Bilateral Filter
```python
def joint_bilateral_filter(image, guide):
    filtered = zeros_like(image)

    for 각 픽셀 (x, y):
        center_guide = guide[y, x]  # ★ guide 사용!

        for 주변 픽셀 (x', y'):
            # Gs: 거리 (동일)
            Gs = exp(-distance² / (2×σ_s²))

            # Gr: 다른 이미지(guide)의 값 차이 ★★
            neighbor_guide = guide[y', x']
            Gr = exp(-(center_guide - neighbor_guide)² / (2×σ_r²))

            weight = Gs × Gr
            filtered[y, x] += image[y', x'] × weight  # image 필터링

    return filtered / normalize
```

**차이점:**
```
Bilateral:
  Gr = exp(-(image[중심] - image[주변])² / (2×σ_r²))
           ↑           ↑
        같은 이미지

Joint Bilateral:
  Gr = exp(-(guide[중심] - guide[주변])² / (2×σ_r²))
           ↑           ↑
        다른 이미지 (guide)!
```

---

## 3. PA1에서의 실제 사용

### 3.1 상황

**필터링 대상:** Cost volume (H×W×64)
```
cost_vol[y, x, d] = 매칭 비용
- 값이 작을수록 잘 매칭됨
- 경계 정보가 없음 (그냥 숫자)
```

**Guide 이미지:** Left image (H×W)
```
left[y, x] = 밝기 값
- 경계가 명확히 보임
- 물체와 배경 구분 가능
```

### 3.2 만약 Bilateral Filter를 사용한다면?

```python
# Cost volume 자체를 보고 Gr 계산
for d in range(64):
    cost_slice = cost_vol[:, :, d]

    # Bilateral filter (잘못된 방법)
    filtered = bilateral_filter(cost_slice)
    # Gr = exp(-(cost_slice[중심] - cost_slice[주변])²)
    #        ↑ cost 값의 차이를 봄

문제:
- Cost 값의 차이는 경계와 무관!
- 물체와 배경의 cost가 우연히 비슷하면 섞임
- 물체 내에서 cost가 차이 나면 안 섞임
→ 엉망!
```

### 3.3 Joint Bilateral Filter 사용 (올바른 방법)

```python
# Guide (left image)를 보고 Gr 계산
for d in range(64):
    cost_slice = cost_vol[:, :, d]
    guide = left_image  # ★ guide 사용

    # Joint bilateral filter (올바른 방법)
    filtered = joint_bilateral_filter(cost_slice, guide)
    # Gr = exp(-(guide[중심] - guide[주변])²)
    #        ↑ guide 이미지의 값 차이를 봄

효과:
- Guide의 경계를 보고 판단
- 물체 내에서는 cost 섞음 (guide 값 비슷)
- 배경과는 cost 안 섞음 (guide 값 다름)
→ 완벽!
```

---

## 4. 시각적 비교

### 4.1 Bilateral Filter on Cost Volume (잘못됨)

```
Left image (guide, 밝기):
  100  100  100 | 200  200  200
  100  100 [X] | 200  200  200
  100  100  100 | 200  200  200
  물체          | 배경

Cost volume (d=30):
  5    5    5   | 50   50   50
  5    5   [5]  | 50   50   50
  5    5    5   | 50   50   50
  물체 cost     | 배경 cost

Bilateral Filter (cost 자체의 차이로 Gr 계산):
  중심 cost = 5
  왼쪽 cost = 5  → 차이 0  → Gr = 1.0 ✅
  오른쪽 cost = 50 → 차이 45 → Gr = 0.0 ✅

결과: 우연히 잘 작동 (cost가 달라서)

BUT! 만약 cost가 비슷하다면?
  물체 cost: 30
  배경 cost: 35  → 차이 5 → Gr = 0.9
  → 물체와 배경이 섞임! ❌
```

### 4.2 Joint Bilateral Filter (올바름)

```
Left image (guide):
  100  100  100 | 200  200  200
  100  100 [X] | 200  200  200
  100  100  100 | 200  200  200

Cost volume (d=30):
  5    5    5   | 50   50   50
  5    5   [5]  | 50   50   50
  5    5    5   | 50   50   50

Joint Bilateral Filter (guide 차이로 Gr 계산):
  중심 guide = 100
  왼쪽 guide = 100 → 차이 0   → Gr = 1.0 ✅
  오른쪽 guide = 200 → 차이 100 → Gr = 0.0 ✅

결과: 항상 잘 작동 (guide가 경계를 정확히 알려줌)

Cost가 어떻든 상관없음:
  물체 cost: 5, 10, 30, 50 아무거나
  배경 cost: 3, 8, 35, 60 아무거나
  → Guide가 100 vs 200이면 무조건 안 섞음! ✅
```

---

## 5. 완전 정리

### 5.1 핵심 차이 표

| 측면 | Bilateral Filter | Joint Bilateral Filter |
|------|------------------|------------------------|
| **필터링 대상** | image | image |
| **Gs 계산 기준** | 거리 | 거리 (동일) |
| **Gr 계산 기준** | **image 자신의 값** | **guide 이미지의 값** ★ |
| **용도** | 일반 이미지 smoothing | 다른 정보 참고한 smoothing |
| **PA1 사용** | ❌ 부적합 | ✅ 완벽 |

### 5.2 수식 비교

**Bilateral Filter:**
```
filtered(x,y) = Σ image(x',y') × Gs × Gr / W

여기서:
Gs = exp(-거리² / 2σ_s²)
Gr = exp(-(image(x,y) - image(x',y'))² / 2σ_r²)
                ↑             ↑
             같은 이미지
```

**Joint Bilateral Filter:**
```
filtered(x,y) = Σ image(x',y') × Gs × Gr / W

여기서:
Gs = exp(-거리² / 2σ_s²)
Gr = exp(-(guide(x,y) - guide(x',y'))² / 2σ_r²)
                ↑             ↑
           다른 이미지 (guide)
```

### 5.3 PA1에서의 실제 코드

**Joint Bilateral Filter:**
```python
def joint_bilateral_slice_numpy(src, guide, ...):
    # src: 필터링할 대상 (cost volume slice)
    # guide: 참고할 이미지 (left image)

    for y in range(H):
        for x in range(W):
            g0 = guide[y+pad, x+pad]  # ★ guide의 중심 값

            src_patch = src[y:y+ksize, x:x+ksize]      # 필터링 대상
            guide_patch = guide[y:y+ksize, x:x+ksize]  # guide

            # Gr: guide의 값 차이로 계산 ★
            Gr = np.exp(-((guide_patch - g0)**2) / (2 * sigma_r**2))

            # 가중치 = Gs × Gr
            Wgt = Gs * Gr

            # src를 가중 평균 (guide는 참고만)
            s = (src_patch * Wgt).sum()
            out[y, x] = s / Wgt.sum()

    return out
```

**핵심:**
1. **필터링 대상**: `src` (cost volume)
2. **Gr 계산 기준**: `guide` (left image) ★
3. **결과**: `src`가 부드러워지되, `guide`의 경계 보존

---

## 6. 마지막 비유

### Bilateral Filter
```
요리사가 요리의 맛을 보고
"비슷한 맛끼리 섞자"
→ 요리 자체의 맛이 기준
```

### Joint Bilateral Filter
```
요리사가 레시피를 보고
"레시피에서 같은 재료끼리 섞자"
→ 레시피(guide)가 기준
```

**PA1에서:**
- 요리 = Cost volume (맛이 엉망진창)
- 레시피 = Left image (명확한 경계 정보)
→ 레시피를 보고 섞어야 함! (Joint Bilateral)

---

## 7. 최종 답변

### Q1: Bilateral filter는 Gs와 Gr을 어떻게 섞어서 계산?
**A**: **곱해서** 사용합니다 (섞는다는 표현보다는 곱셈)

```python
weight = Gs × Gr

- Gs: 거리 가까울수록 높음
- Gr: 픽셀 값 비슷할수록 높음
- weight: 두 조건 모두 만족해야 높음

예:
- 거리 가깝고(Gs=0.9) + 값 비슷(Gr=0.8) = weight: 0.72 (높음) ✅
- 거리 가깝지만(Gs=0.9) + 값 다름(Gr=0.1) = weight: 0.09 (낮음) ❌
```

### Q2: Joint bilateral filter는 무엇이 달라진 것?
**A**: **Gr 계산에 다른 이미지(guide)를 사용**

```
Bilateral:
  Gr = 필터링할 이미지 자신의 값 차이
  → image[중심] vs image[주변]

Joint Bilateral:
  Gr = 다른 이미지(guide)의 값 차이
  → guide[중심] vs guide[주변]

PA1:
  필터링할 것: cost volume (경계 정보 없음)
  Guide: left image (경계 정보 명확)
  → left image의 경계 정보로 cost를 섞을지 결정!
```

---

**이제 완전히 이해하셨나요?** 🎯

핵심만 기억하세요:
1. Bilateral: 자기 자신을 보고 Gr 계산
2. Joint Bilateral: 다른 이미지(guide)를 보고 Gr 계산
3. PA1: cost volume은 경계 정보 없음 → guide(left image) 필요!
