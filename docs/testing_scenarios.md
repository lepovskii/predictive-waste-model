# Testing Scenarios & Validation

_Last updated: 2026-07-17_

This document records the final black-box testing scenarios and philosophical approaches for handling data anomalies (dirty data) within the Predictive Waste Model system.

## 1. Input Validation & Data Adapter Testing

These scenarios verify the system's ability to reject invalid payloads and correctly process adapter preview files, ensuring robust data validation before any inference is made.

| Skenario | Endpoint/Halaman | Deskripsi & Langkah | Hasil yang Diharapkan |
|---|---|---|---|
| (a) Respons HTTP 409 (Duplikat) | `POST /predict` | Mengirim payload dengan `production_date` yang sudah ada di database. | Sistem menolak dengan HTTP 409 Conflict. Mencegah duplikasi data. |
| (b) Respons HTTP 422 (Shutdown) | `POST /predict` | Mengirim profil bernama `Shutdown` yang melanggar konstrain Pydantic. | Sistem merespons dengan HTTP 422 Unprocessable Entity. Profil diabaikan. |
| (c) Respons HTTP 404 (Task ID Palsu) | `GET /status/{task_id}` | Memeriksa status menggunakan UUID palsu. | Sistem merespons dengan HTTP 404 Not Found. |
| (d) Adapter VALID | Halaman Upload UI | Mengunggah CSV yang terformat benar (contoh: `januari_2023.csv`). | Adapter merespons dengan status VALID dan `is_valid_for_prediction=true`. |
| (e) Adapter INVALID (Dirty Data) | Halaman Upload UI | Mengunggah dataset dengan inkonsistensi manusia (contoh: `desember_2023.csv`). | Adapter mendeteksi kesalahan, merespons dengan INVALID, dan `is_valid_for_prediction=false`. |

### Case Study Skenario 1(e): "Dirty Data" sebagai Bukti Ketahanan Sistem
Dalam pengujian dataset `desember_2023.csv`, ditemukan bahwa operator lapangan mengosongkan kolom aktual produksi (`Prod Act (Ton)`) sepenuhnya dan salah memasukkan datanya ke kolom target (`Production (Ton)`). 

Alih-alih memanipulasi kode dengan menambahkan "Smart Fallback" (yang secara diam-diam memindahkan pembacaan dari kolom target jika kolom aktual kosong), diputuskan bahwa **adapter harus secara ketat menolak data ini**. 
Keputusan ini memperkuat narasi akademis dalam skripsi bahwa:
1. Praktik manual (*human error*) dalam pelaporan pabrik nyata sangat rawan inkonsistensi.
2. Sistem yang dirancang bertindak sebagai "penjaga gerbang" (*gatekeeper*) yang tangguh, mencegah masuknya data cacat (*dirty data*) ke dalam model Machine Learning yang bisa mengakibatkan bias prediksi.
3. Menunjukkan bahwa sistem hanya akan memproses data yang dapat dipertanggungjawabkan kebenarannya.

## 2. Asynchronous Prediction Flow & Reconciliation

These scenarios ensure that the asynchronous architecture (Celery/Redis) handles batch background jobs reliably, and that predictions can be reconciled with actual values later.

| Skenario | Endpoint/Halaman | Deskripsi & Langkah | Hasil yang Diharapkan |
|---|---|---|---|
| (a) Task ID Creation | `POST /predict` atau `/predict/batch` | Mengirim batch data valid yang baru. | Menerima HTTP 202 Accepted yang berisi array hasil proses dan `task_id` untuk pelacakan asinkron. |
| (b) Celery Worker Logging | Docker logs `worker` | Memeriksa log *container* celery. | Terlihat jejak penerimaan task dan penyelesaian (*succeeded*) tanpa error. |
| (c) Status DRAFT | `GET /status/{task_id}` | Mengambil data status UUID yang selesai. | Sistem merespons dengan state `"DRAFT"`, menandakan prediksi telah disimpan. |
| (d) Halaman Detail (Pre-Reconciliation) | Halaman History UI | Membuka detail produksi yang berstatus DRAFT. | UI menampilkan prediksi dari AI, dengan *form input* aktual yang masih kosong atau terbuka untuk diedit. |
| (e) Halaman Detail (RECONCILED) | Halaman History UI | Mengisi nilai aktual (WIP & Prime) di form dan menyimpannya ke `/reconcile`. | Status berubah menjadi `"RECONCILED"`. UI mengunci form input dan menampilkan *Absolute Error* antara AI vs Aktual. |

---
*Dokumentasi ini ditulis sebagai bagian pelengkap persiapan penyusunan laporan skripsi (Bab 4/Bab 5) terkait pengujian fungsional.*
