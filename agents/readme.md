# Automated Code Debugger & Bug Finder

Project Tugas Besar Kecerdasan Buatan (IF-504)

Sistem Automated Code Debugger merupakan aplikasi berbasis Python yang menggunakan konsep **Agentic AI** untuk mendeteksi, menganalisis, dan memperbaiki kesalahan pada source code Python secara otomatis.

Sistem ini menggunakan:
- Python sebagai bahasa pemrograman utama.
- LangGraph untuk mengatur alur kerja multi-agent.
- LangChain untuk mengintegrasikan Large Language Model.
- Ollama untuk menjalankan AI secara lokal.
- Qwen 2.5:7b sebagai model bahasa.
- nomic-embed-text untuk menghasilkan embedding.
- ChromaDB sebagai vector database untuk menyimpan Knowledge Base.

---

## 1. Prerequisites

Pastikan perangkat sudah memiliki:

1. Python 3.10 atau lebih baru.
2. Visual Studio Code.
3. Ollama.
4. Git (opsional).

Model AI yang digunakan:

| Model | Fungsi |
|---|---|
| `qwen2.5:7b` | Menganalisis dan memperbaiki kode serta melakukan Query Rewriting |
| `nomic-embed-text` | Mengubah dokumen Knowledge Base dan query menjadi embedding |

## 2. Installation & Setup

### Step 1 — Clone atau buka project

Buka terminal VS Code dan masuk ke folder project:

```powershell
cd C:\Semester_5\AI\tubes_ai\tubes_ai
```

Pastikan terminal berada di folder utama project yang berisi `main.py`.

### Step 2 — Membuat Virtual Environment

Buat virtual environment:

```powershell
python -m venv .venv
```

Aktifkan virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Jika berhasil, terminal akan menampilkan prefix:

```text
(.venv) PS C:\...
```

### Step 3 — Install Dependencies

Install library yang dibutuhkan:

```powershell
pip install langchain langchain-core langchain-ollama langchain-chroma langgraph chromadb
```

Jika project sudah menyediakan `requirements.txt`, gunakan:

```powershell
pip install -r requirements.txt
```

### Step 4 — Install dan Jalankan Ollama

Download Ollama melalui:

https://ollama.com/download

Setelah instalasi, download model yang dibutuhkan:

```powershell
ollama pull qwen2.5:7b
```

```powershell
ollama pull nomic-embed-text
```

Pastikan kedua model sudah terpasang:

```powershell
ollama list
```

Model yang harus tersedia:

```text
qwen2.5:7b
nomic-embed-text
```

Ollama harus berjalan ketika aplikasi digunakan. Pada Windows, Ollama biasanya berjalan melalui aplikasi background setelah dibuka.

### Step 5 — Jalankan Program

Pastikan virtual environment aktif dan terminal berada di folder utama project.

Jalankan:

```powershell
python main.py
```

Jika berhasil, akan muncul menu:

```text
========== AVAILABLE TEST CASES ==========

1. valid
2. zerodivision
3. indexerror
4. keyerror
5. syntax
6. attributeerror

Select test case:
```

Masukkan nama test case, misalnya:

```text
zerodivision
```

Sistem akan mulai melakukan proses debugging.

---

## 3. Project Structure

```text
tubes_ai/
│
├── agents/
│   ├── syntax_checker.py
│   ├── supervisor.py
│   ├── rag_specialist.py
│   └── code_fixer.py
│
├── tools/
│   ├── syntax_tool.py
│   ├── execution_tool.py
│   └── trace_logger.py
│
├── knowledge_base/
│   ├── syntax_errors.txt
│   ├── runtime_errors.txt
│   └── debugging_guide.txt
│
├── workspace/
│   ├── buggy_code.py
│   └── fixed_code.py
│
├── chroma_db/
│
├── state.py
├── graph.py
├── main.py
├── test_case.py
└── README.md
```

### Fungsi Setiap File

| File / Folder | Fungsi |
|---|---|
| `main.py` | Entry point untuk menjalankan aplikasi dan menangani persetujuan pengguna |
| `state.py` | Menyimpan struktur state yang digunakan antar-agent |
| `graph.py` | Mengatur workflow, node, edge, routing, dan Human-in-the-Loop |
| `test_case.py` | Menyediakan contoh source code dengan berbagai jenis error |
| `agents/syntax_checker.py` | Mendeteksi syntax error dan runtime error |
| `agents/rag_specialist.py` | Mencari solusi dari Knowledge Base menggunakan RAG |
| `agents/code_fixer.py` | Menghasilkan source code yang sudah diperbaiki |
| `agents/supervisor.py` | Menentukan agent berikutnya berdasarkan hasil proses |
| `tools/syntax_tool.py` | Membantu pemeriksaan syntax Python |
| `tools/execution_tool.py` | Menjalankan source code untuk mendeteksi runtime error |
| `tools/trace_logger.py` | Mencatat proses Thought, Action, dan Observation |
| `knowledge_base/` | Menyimpan dokumentasi error dan strategi debugging |
| `chroma_db/` | Menyimpan vector database hasil embedding Knowledge Base |
| `workspace/buggy_code.py` | File source code yang sedang diperiksa |
| `workspace/fixed_code.py` | File hasil perbaikan dari Code Fixer |

---

## 4. System Architecture

Sistem menggunakan arsitektur **Supervisor-Worker Multi-Agent** dengan LangGraph.

Setiap agent memiliki tugas masing-masing. Supervisor bertugas mengatur perpindahan antar-agent berdasarkan hasil diagnosis dan proses perbaikan.

### Agent Components

**1. Syntax Checker**

Bertugas memeriksa source code sebelum proses perbaikan.

Proses:
- Memeriksa syntax menggunakan Python AST.
- Jika syntax valid, kode dapat dieksekusi untuk mendeteksi runtime error.
- Mengidentifikasi jenis error dan informasi pendukung seperti pesan error serta baris kode yang bermasalah.

Contoh:

```python
x = 10
y = 0

print(x / y)
```

Hasil diagnosis:

```text
Error Type: ZeroDivisionError
```

Jika source code tidak memiliki error, workflow dapat langsung dihentikan tanpa menjalankan RAG dan Code Fixer.

**2. RAG Specialist**

Bertugas mencari solusi berdasarkan dokumentasi yang tersimpan di Knowledge Base.

RAG menggunakan dua proses utama:

- Retrieval: mencari dokumen yang relevan menggunakan ChromaDB.
- Augmentation: memberikan informasi hasil pencarian kepada Code Fixer sebagai referensi perbaikan.

Knowledge Base terdiri dari:

| File | Isi |
|---|---|
| `syntax_errors.txt` | Informasi dan solusi syntax error |
| `runtime_errors.txt` | Informasi dan solusi runtime error |
| `debugging_guide.txt` | Strategi dan panduan debugging |

Konfigurasi retrieval:

```python
k = 2
DISTANCE_THRESHOLD = 0.5
```

Artinya:
- Sistem mengambil maksimal dua dokumen terdekat.
- Dokumen hanya diterima jika distance score tidak lebih besar dari 0.5.
- Dokumen yang tidak memenuhi threshold tidak diberikan kepada Code Fixer.

*Catatan: Threshold 0.5 merupakan konfigurasi pengujian saat ini, bukan nilai optimal untuk semua jenis error.*

**Agentic RAG — Query Rewriting**

Jika pencarian pertama menghasilkan `NOT_FOUND`, RAG Specialist meminta Qwen untuk membuat query baru.

Alurnya:

```text
Initial Search
      |
      v
  ChromaDB
      |
      v
 Documents Found?
    /       \
  YES        NO
   |          |
   v          v
  FOUND    Query Rewriting
              |
              v
          Search Again
              |
              v
        Documents Found?
           /      \
         YES       NO
          |         |
          v         v
        FOUND   NOT_FOUND
                    |
                    v
              Code Fixer
```

Sistem memiliki batas maksimal dua percobaan pencarian. Jika pencarian tetap tidak menemukan dokumen relevan, Supervisor dapat mengarahkan proses ke Code Fixer menggunakan informasi diagnosis yang tersedia.

**3. Code Fixer**

Bertugas menghasilkan source code yang sudah diperbaiki.

Input:
- Source code awal.
- Jenis error.
- Pesan error.
- Baris kode yang bermasalah.
- Informasi dari Knowledge Base jika tersedia.

Code Fixer menggunakan Qwen 2.5:7b untuk menghasilkan perbaikan.

Hasilnya disimpan di:

```text
workspace/fixed_code.py
```

**4. Supervisor**

Supervisor mengatur jalannya workflow.

Tugasnya:
- Menerima hasil diagnosis.
- Menentukan apakah perlu menjalankan RAG Specialist.
- Menentukan kapan Code Fixer harus dijalankan.
- Mengatur proses validasi.
- Menghentikan workflow jika tidak ada perbaikan yang diperlukan atau proses gagal.

Supervisor memastikan setiap agent bekerja sesuai urutan dan kondisi yang ditentukan.

**5. Validation**

Setelah Code Fixer menghasilkan source code, sistem melakukan validasi.

Pemeriksaan meliputi:
- Memastikan file hasil perbaikan tidak kosong.
- Memeriksa syntax menggunakan AST.
- Menjalankan kode hasil perbaikan menggunakan subprocess.
- Membatasi waktu eksekusi dengan timeout.

Jika hasil validasi gagal, patch tidak dilanjutkan ke tahap persetujuan.

**6. Human-in-the-Loop**

Sebelum perubahan diterapkan, sistem meminta persetujuan manusia.

Contoh:

```text
========== HUMAN APPROVAL ==========

Proposed Fixed Code:

x = 10
y = 0

if y != 0:
    print(x / y)
else:
    print("Cannot divide by zero")

Apply this patch? (y/n):
```

Jika pengguna memilih:

- `y`: patch disetujui dan source code diperbarui.
- `n`: patch ditolak dan source code awal tidak diperbarui.

Implementasi menggunakan LangGraph `interrupt_before` dan `MemorySaver` agar workflow dapat dihentikan sementara dan dilanjutkan setelah keputusan pengguna.

---

## 5. How the System Works

Berikut alur lengkap sistem dari awal hingga selesai:

```text
        USER SELECTS TEST CASE
                  |
                  v
          SYNTAX CHECKER
                  |
                  v
          Syntax / Runtime
              Error?
            /       \
          NO         YES
          |           |
          v           v
         END      SUPERVISOR
                      |
                      v
                 RAG SPECIALIST
                      |
                      v
                KNOWLEDGE BASE
                      |
                      v
                 RETRIEVAL
                      |
                      v
                Relevant Docs?
                 /        \
               YES         NO
                |           |
                |      QUERY REWRITING
                |           |
                |      RETRIEVAL AGAIN
                |           |
                +-----+-----+
                      |
                      v
                  CODE FIXER
                      |
                      v
                  VALIDATION
                      |
                      v
                 Validation OK?
                   /      \
                 NO        YES
                 |          |
                 v          v
                END     HUMAN APPROVAL
                            |
                       /         \
                     YES          NO
                      |            |
                      v            v
                 APPLY PATCH   REJECT PATCH
                      |            |
                      v            v
                PATCH APPLIED  PATCH REJECTED
```

---

## 6. ReAct Diagnostic Loop

Project ini juga menerapkan konsep ReAct (Reasoning and Acting).

ReAct memiliki tiga tahapan:

1. **Thought** — Agent menentukan tindakan yang perlu dilakukan.
2. **Action** — Agent menjalankan tool atau melakukan pencarian.
3. **Observation** — Agent menerima dan mengevaluasi hasil tindakan.

Contoh:

```text
========== REACT STEP ==========

[THOUGHT]
Agent harus memeriksa syntax Python terlebih dahulu.

[ACTION]
Execute syntax_checker_tool

[OBSERVATION]
{
    "status": "SUCCESS",
    "has_error": true,
    "error_type": "ZeroDivisionError"
}
```

Proses ini dicatat menggunakan `trace_logger.py` sehingga aktivitas agent dapat diperiksa kembali dalam Debug Mode.

---

## 7. Demo Mode & Debug Mode

Aplikasi menyediakan dua mode tampilan.

Pengaturan terdapat di `main.py`:

```python
DEBUG_MODE = False
```

**Demo Mode**

```python
DEBUG_MODE = False
```

Digunakan untuk demonstrasi aplikasi.

Menampilkan:
- Diagnosis error.
- Ringkasan aktivitas setiap agent.
- Hasil validasi.
- Keputusan Human Approval.
- Hasil akhir patch.

**Debug Mode**

```python
DEBUG_MODE = True
```

Digunakan untuk memeriksa proses internal sistem.

Menampilkan:
- Detail proses setiap agent.
- Query RAG.
- Distance score ChromaDB.
- Hasil Query Rewriting.
- Thought, Action, Observation.
- Supervisor routing.
- Hasil validasi dan patch.

---

## 8. Available Test Cases

Jalankan aplikasi dengan:

```powershell
python main.py
```

Pilih salah satu test case berikut:

| Test Case | Error | Tujuan Pengujian |
|---|---|---|
| `valid` | Tidak ada error | Memastikan kode valid tidak perlu diperbaiki |
| `zerodivision` | ZeroDivisionError | Menguji perbaikan pembagian dengan nol |
| `indexerror` | IndexError | Menguji perbaikan akses index list |
| `keyerror` | KeyError | Menguji perbaikan akses dictionary |
| `syntax` | SyntaxError | Menguji pendeteksian dan perbaikan syntax |
| `attributeerror` | AttributeError | Menguji retrieval dan Query Rewriting |

Untuk pengujian, coba juga kedua pilihan Human Approval:
- Masukkan `y` untuk menyetujui patch.
- Masukkan `n` untuk menolak patch.

Dengan demikian, sistem dapat menunjukkan bahwa keputusan manusia benar-benar memengaruhi penerapan perbaikan.

---

## 9. Important Notes

**1. Knowledge Base berubah**

ChromaDB menggunakan persistent storage di folder `chroma_db`.

Jika isi file Knowledge Base diubah, database lama tidak otomatis diperbarui oleh program saat ini.

Untuk membangun ulang database berdasarkan dokumen terbaru:

1. Hentikan aplikasi.
2. Hapus folder `chroma_db`.
3. Jalankan kembali:

```powershell
python main.py
```

Sistem akan membuat vector database baru dari dokumen Knowledge Base.

**2. Human Approval**

Jangan menganggap kode yang lolos Validation otomatis diterapkan.

Patch hanya diterapkan jika pengguna menyetujuinya.

**3. Ollama**

Pastikan Ollama aktif dan kedua model sudah tersedia sebelum menjalankan aplikasi.

**4. Workspace**

File `buggy_code.py` merupakan target source code yang digunakan dalam proses debugging. File `fixed_code.py` merupakan hasil perbaikan yang dibuat oleh Code Fixer.

---

## 10. Troubleshooting

| Kendala | Solusi |
|---|---|
| `ModuleNotFoundError` | Aktifkan `.venv` dan install dependencies |
| Ollama connection error | Pastikan aplikasi Ollama berjalan |
| Model not found | Jalankan `ollama pull qwen2.5:7b` atau `ollama pull nomic-embed-text` |
| ChromaDB tidak memperbarui dokumen | Hapus folder `chroma_db`, lalu jalankan ulang aplikasi |
| Syntax atau runtime error saat menjalankan aplikasi | Periksa traceback dan file yang disebutkan |
| Query Rewriting tidak berjalan | Periksa hasil retrieval, threshold, dan batas pencarian pada RAG Specialist |

---

## 11. Project Summary

Automated Code Debugger menggabungkan beberapa konsep Agentic AI dalam satu workflow:

| Konsep | Implementasi |
|---|---|
| ReAct | Thought → Action → Observation |
| Agentic RAG | ChromaDB retrieval dan Query Rewriting |
| Multi-Agent System | Supervisor dan worker agents |
| StateGraph | Pengaturan workflow menggunakan LangGraph |
| Human-in-the-Loop | Persetujuan sebelum patch diterapkan |
| Local LLM | Qwen 2.5:7b melalui Ollama |
| Vector Database | ChromaDB |
| Validation | AST dan subprocess execution |

**Tujuan akhir sistem:** mendeteksi kesalahan Python, mencari referensi solusi, menghasilkan perbaikan secara otomatis, memvalidasi hasil perbaikan, dan meminta persetujuan manusia sebelum mengubah source code awal.

---

**End of README**