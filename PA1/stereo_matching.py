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
        #TODO1: image shift
        r_shift = shift_right_image(right_f, d)

        #TODO2: SAD
        diff = np.abs(left_f - r_shift)

        cost_vol[:, :, d] = diff

        if d > 0:
            cost_vol[:, :d, d] = 1e6 # 우측 이미지를 d만큼 shift해, zero padding된 영역의 cost를 무한대로 설정

    return cost_vol

def aggregate_cost_volume_box(cost_vol, window_size=7):
    h, w, D = cost_vol.shape
    agg = np.zeros_like(cost_vol)
    k = (window_size, window_size)
    for d in range(D):
        #TODO3: aggregate cost volume
        agg[:, :, d] = cv2.boxFilter(cost_vol[:, :, d], -1, k) # cv.BoxFilter(d번째 disparity의 cost map, 데이터 타입 유지(-1), 윈도우 사이즈 k)
    return agg

def select_disparity(agg_cost_vol):
    #TODO4: select disparity
    disp = np.argmin(agg_cost_vol, axis=2) # disparity 차원에서의 최소값 인덱스 반환
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
    guide = (guide_gray.astype(np.float32) / 255.0).copy() # 0-1 정규화
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
                 max_disp=64, window_size=7):
    left  = load_gray(left_path)
    right = load_gray(right_path)

    cost_vol = build_cost_volume(left, right, max_disp=max_disp)

    #TODO6: Joint Bilateral Filter (채우지 않아도 코드는 실행 가능)


    agg_cost_vol = aggregate_cost_volume_box(cost_vol, window_size=window_size)

    disp = select_disparity(agg_cost_vol)

    
    #TODO7: Weighted Median Filter (채우지 않아도 코드는 실행 가능)
    #disp = weighted_median_disparity_numpy(disp, left, win_radius=3, sigma_s=3.0, sigma_r=0.08)


    disp_vis = cv2.normalize(disp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return disp, disp_vis

if __name__ == "__main__":
    left_path  = "images/reindeer_left.png"
    right_path = "images/reindeer_right.png"
    output_path = "output/reindeer_disparity.png"

    disp_sad, disp_sad_vis = stereo_match(left_path, right_path,
                                          max_disp=64, window_size=3)
    cv2.imwrite(output_path, disp_sad_vis)

    print("저장됨: " + output_path)