from typing import Optional

import numpy as np


def _lazy_import_matplotlib() -> None:
    import matplotlib  # noqa: F401
    import mpl_toolkits.mplot3d  # noqa: F401


def _read_image_grayscale(path: str) -> np.ndarray:
    import cv2  # type: ignore

    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(f"Failed to read image: {path}")

    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def plot_disparity_3d(
    disparity: np.ndarray,
    rgb: Optional[np.ndarray] = None,
    downsample: int = 2,
    mode: str = "surface",
    cmap: str = "inferno",
    invert_height: bool = False,
) -> None:
    """
    Render a 2D disparity map as a 3D plot.

    disparity: (H, W) numeric array
    downsample: integer factor to subsample for speed
    mode: 'surface' or 'point'
    cmap: matplotlib colormap name
    invert_height: if True, uses -disparity as Z so larger disparity pops out
    """
    if disparity.ndim != 2:
        raise ValueError("disparity must be a 2D array")

    _lazy_import_matplotlib()
    import matplotlib.pyplot as plt  # imported after check

    disparity_float = disparity.astype(np.float32)
    valid_mask = np.isfinite(disparity_float) & (disparity_float > 0)

    # Prepare RGB texture if provided
    if rgb is not None:
        if rgb.ndim != 3 or rgb.shape[2] not in (3, 4):
            raise ValueError("rgb must be an HxWx3 or HxWx4 array")
        if rgb.shape[0] != disparity.shape[0] or rgb.shape[1] != disparity.shape[1]:
            raise ValueError("rgb image must have the same HxW as disparity")
        if rgb.dtype == np.uint8:
            rgb_float = rgb.astype(np.float32) / 255.0
        else:
            rgb_float = np.clip(rgb.astype(np.float32), 0.0, 1.0)
    else:
        rgb_float = None

    if downsample > 1:
        disparity_float = disparity_float[::downsample, ::downsample]
        valid_mask = valid_mask[::downsample, ::downsample]
        if rgb_float is not None:
            rgb_float = rgb_float[::downsample, ::downsample]

    height, width = disparity_float.shape
    y_coords = np.arange(height, dtype=np.float32)
    x_coords = np.arange(width, dtype=np.float32)
    X, Y = np.meshgrid(x_coords, y_coords)

    Z = -disparity_float if invert_height else disparity_float

    # Auto color scale for disparity when not using RGB texture
    if np.any(valid_mask):
        valid_values = disparity_float[valid_mask]
        vmin = float(np.nanpercentile(valid_values, 1))
        vmax = float(np.nanpercentile(valid_values, 99))
    else:
        vmin = 0.0
        vmax = 1.0

    if mode not in {"surface", "point"}:
        raise ValueError("mode must be 'surface' or 'point'")

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    if mode == "surface":
        Z_plot = np.where(valid_mask, Z, np.nan)
        facecolors = None
        if rgb_float is not None:
            # Build RGBA where invalid points are transparent
            if rgb_float.shape[2] == 3:
                alpha = (valid_mask.astype(np.float32))[..., None]
                rgba = np.concatenate([rgb_float, alpha], axis=2)
            else:
                rgba = rgb_float.copy()
                rgba[..., 3] = np.where(valid_mask, rgba[..., 3], 0.0)
            facecolors = rgba

        surf = ax.plot_surface(
            X,
            Y,
            Z_plot,
            cmap=None if facecolors is not None else cmap,
            facecolors=facecolors,
            linewidth=0,
            antialiased=True,
            vmin=vmin if facecolors is None else None,
            vmax=vmax if facecolors is None else None,
        )
        if facecolors is None:
            cbar = fig.colorbar(surf, ax=ax, shrink=0.6, pad=0.1)
    else:
        Xv = X[valid_mask]
        Yv = Y[valid_mask]
        Zv = Z[valid_mask]
        if rgb_float is not None:
            Cv = rgb_float[valid_mask]
            pts = ax.scatter(Xv, Yv, Zv, c=Cv, s=1.0, alpha=0.95)
        else:
            pts = ax.scatter(
                Xv, Yv, Zv, c=Zv, s=1.0, cmap=cmap, vmin=vmin, vmax=vmax, alpha=0.9
            )
            cbar = fig.colorbar(pts, ax=ax, shrink=0.6, pad=0.1)

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("disparity")
    if "cbar" in locals():
        cbar.set_label("disparity")
    ax.view_init(elev=60, azim=-60)
    plt.tight_layout()
    plt.show()
def _read_image_color_rgb(path: str) -> np.ndarray:
    import cv2  # type: ignore
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(f"Failed to read image: {path}")
    return bgr[:, :, ::-1]


def main() -> None:
    # Simple, argument-free demo: adjust paths if needed
    disparity_path = "output/reindeer_disparity.png"
    rgb_path = "images/reindeer_left.png"  # set to None to disable RGB coloring

    disparity_image = _read_image_grayscale(disparity_path)
    rgb_image = None
    if rgb_path is not None:
        rgb_image = _read_image_color_rgb(rgb_path)

    plot_disparity_3d(
        disparity_image,
        rgb=rgb_image,
        downsample=2,
        mode="surface",
        cmap="inferno",
        invert_height=True,
    )


if __name__ == "__main__":
    main()


