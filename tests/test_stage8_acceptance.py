# -*- coding: utf-8 -*-
"""
Kiểm thử Giai đoạn 8: Nghiệm thu Chuẩn NFR-05 & Tính năng Bổ sung
- Kiểm tra tính toán sai số khoảng cách so với ngưỡng +-5cm
- Kiểm tra độ chính xác nhận diện Camera so với ngưỡng 90%
- Kiểm tra xuất báo cáo Excel (.xlsx) qua openpyxl
"""

import os
import pytest
import openpyxl

import database
from tools.eval_accuracy import evaluate_radar_distance_accuracy, evaluate_detector_accuracy


def test_distance_accuracy_evaluation_against_nfr05(tmp_path):
    """NFR-05: Sai số đo khoảng cách phải nằm trong ngưỡng +-5cm (+-0.05m)"""
    csv_out = str(tmp_path / "dist_test.csv")
    passed = evaluate_radar_distance_accuracy(csv_output_path=csv_out)
    assert passed is True
    assert os.path.exists(csv_out)


def test_detector_accuracy_evaluation_against_nfr05():
    """NFR-05: Tỉ lệ nhận diện đối tượng đúng phải đạt từ 90% trở lên"""
    model_path = os.path.join(os.path.dirname(__file__), "..", "models", "yolov8n.onnx")
    passed = evaluate_detector_accuracy(model_path=model_path)
    assert passed is True


def test_excel_export_incidents(tmp_path, monkeypatch):
    """Kiểm tra xuất báo cáo định dạng Excel .xlsx hợp lệ kèm tiêu đề và định dạng"""
    db_file = str(tmp_path / "test_excel.db")
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()

    # Thêm 2 sự cố mẫu
    database.insert_incident(
        start_time="2026-11-11 08:30:00",
        end_time="2026-11-11 08:30:03",
        max_severity="ĐỎ - Nguy cơ va chạm",
        object_type="Ô tô",
        min_distance_m=1.2,
        min_ttc_sec=1.1,
        max_speed_kmh=24.5,
        image_path="",
        notes="kiểm thử xuất excel"
    )

    xlsx_path = str(tmp_path / "test_report.xlsx")
    count = database.export_to_excel(xlsx_path)

    assert count == 1
    assert os.path.exists(xlsx_path)

    # Đọc lại bằng openpyxl để xác minh
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active
    assert ws.title == "Nhat_Ky_Su_Co"
    # Dòng 1 là headers, dòng 2 là dữ liệu
    assert ws.max_row == 2
    assert "Mã sự cố" in ws.cell(row=1, column=1).value
    assert ws.cell(row=2, column=4).value == "Ô tô"
