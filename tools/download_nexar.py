# -*- coding: utf-8 -*-
"""
Công cụ tải chọn lọc 10 video mẫu đa dạng bối cảnh (Ngày / Đêm / Mưa / Chạng vạng / Đô thị / Cao tốc)
từ Hugging Face dataset `nexar-ai/nexar_collision_prediction` -> captures/nexar_samples
"""

import os
from huggingface_hub import HfApi, hf_hub_download

REPO_ID = "nexar-ai/nexar_collision_prediction"
OUT_DIR = r"C:\CNPM_Project\captures\nexar_samples"

SELECTED_TARGETS = [
    "train/positive/metadata.csv",
    "train/negative/metadata.csv",
    # 6 video positive (có sự cố / suýt va chạm)
    "train/positive/00000.mp4",  # Urban, Normal, Clear
    "train/positive/00003.mp4",  # Highway, Normal, Rain
    "train/positive/00004.mp4",  # Urban, Normal, Cloudy
    "train/positive/00927.mp4",  # Urban, Dark (ban đêm), Clear
    "train/positive/00629.mp4",  # Sub-urban, Twilight (chạng vạng), alert ~8.4s
    "train/positive/00205.mp4",  # Highway, Normal, Clear
    # 4 video negative (lái xe bình thường)
    "train/negative/01040.mp4",  # Urban, Normal, Cloudy
    "train/negative/01041.mp4",  # Sub-urban, Normal, Cloudy
    "train/negative/02049.mp4",  # Sub-urban, Dark (ban đêm), Clear
    "train/negative/01429.mp4",  # Urban, Normal, Rain
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    api = HfApi()
    repo_files = set(api.list_repo_files(repo_id=REPO_ID, repo_type="dataset"))

    downloaded_videos = 0
    for rel_path in SELECTED_TARGETS:
        if rel_path not in repo_files:
            print(f"[BỎ QUA] Không thấy trên repo: {rel_path}")
            continue
        local_check = os.path.join(OUT_DIR, rel_path.replace("/", os.sep))
        if os.path.exists(local_check):
            print(f"[ĐÃ CÓ] {rel_path}")
            if rel_path.endswith(".mp4"):
                downloaded_videos += 1
            continue
        print(f"Đang tải: {rel_path}")
        local_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=rel_path,
            repo_type="dataset",
            local_dir=OUT_DIR,
        )
        print(f"  -> OK: {local_path}")
        if rel_path.endswith(".mp4"):
            downloaded_videos += 1

    print(f"\nHoàn tất! Tổng cộng {downloaded_videos} video mẫu tại: {OUT_DIR}")


if __name__ == "__main__":
    main()
