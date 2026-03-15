"""
services/dicom_analyzer_optimized.py
─────────────────────────────────────────────────────────────────────────────
Optimized DICOM batch analyzer for HALO Core.

Drop this file next to services/dicom_analyzer.py (the existing service).
It exposes two public functions that both return the same result shape so
the Streamlit benchmark page can call them side-by-side:

    analyze_naive(paths)      – sequential, full pixel read (baseline)
    analyze_optimized(paths)  – parallel workers + stop_before_pixels + cache

Benchmark helpers
─────────────────
    BenchmarkResult           – dataclass returned by both analyzers
    format_benchmark_table()  – render a human-readable comparison string
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

HALO_DATA_DIR = Path(os.environ.get("HALO_DATA_DIR", "data"))
CACHE_PATH = HALO_DATA_DIR / "dicom_opt_cache.db"  # SQLite (replaces legacy .json)
_LEGACY_JSON_CACHE = HALO_DATA_DIR / "dicom_opt_cache.json"  # migrated on first run

# Tags we actually care about – skipping unused tags is free speed.
# Must be (group, element) tuples or pydicom Tag objects; plain strings are
# NOT recognised by specific_tags and would cause a full-tag read.
ANALYSIS_TAGS = [
    (0x0010, 0x0020),  # PatientID
    (0x0010, 0x0010),  # PatientName
    (0x0010, 0x0030),  # PatientBirthDate
    (0x0010, 0x0040),  # PatientSex
    (0x0008, 0x0080),  # InstitutionName
    (0x0008, 0x0020),  # StudyDate
    (0x0008, 0x1030),  # StudyDescription
    (0x0020, 0x000D),  # StudyInstanceUID
    (0x0020, 0x000E),  # SeriesInstanceUID
    (0x0008, 0x0018),  # SOPInstanceUID
    (0x0008, 0x0060),  # Modality
    (0x0008, 0x0070),  # Manufacturer
    (0x0018, 0x0015),  # BodyPartExamined
    (0x0018, 0x0050),  # SliceThickness
    (0x0028, 0x0030),  # PixelSpacing
    (0x0028, 0x0010),  # Rows
    (0x0028, 0x0011),  # Columns
    (0x0028, 0x0100),  # BitsAllocated
]

# Minimum file count where ProcessPoolExecutor spawn overhead (Windows) is
# amortised and parallel processing actually wins over sequential.
PARALLEL_THRESHOLD = 8

# ── Result dataclass ──────────────────────────────────────────────────────────


@dataclass
class DicomRecord:
    file: str
    patient_id: str = ""
    patient_name: str = ""
    patient_birthdate: str = ""
    patient_sex: str = ""
    institution: str = ""
    study_date: str = ""
    study_description: str = ""
    study_uid: str = ""
    series_uid: str = ""
    sop_uid: str = ""
    modality: str = ""
    manufacturer: str = ""
    body_part: str = ""
    slice_thickness: str = ""
    pixel_spacing: str = ""
    rows: int = 0
    columns: int = 0
    bits_allocated: int = 0
    error: str = ""
    from_cache: bool = False


@dataclass
class BenchmarkResult:
    records: list[DicomRecord]
    elapsed_sec: float
    total_files: int
    failed_files: int
    cache_hits: int
    workers_used: int
    strategy: str
    throughput_fps: float = field(init=False)

    def __post_init__(self) -> None:
        self.throughput_fps = (
            round(self.total_files / self.elapsed_sec, 2)
            if self.elapsed_sec > 0
            else 0.0
        )


# ── Internal helpers ──────────────────────────────────────────────────────────


def _safe_str(ds: Any, tag: str) -> str:
    try:
        val = getattr(ds, tag, "")
        return str(val).strip() if val else ""
    except Exception:
        return ""


def _safe_int(ds: Any, tag: str) -> int:
    try:
        return int(getattr(ds, tag, 0) or 0)
    except Exception:
        return 0


def _file_fingerprint(path: str) -> str:
    """Fast fingerprint: first 8 KB + file size (avoids reading full file)."""
    try:
        p = Path(path)
        size = p.stat().st_size
        with open(p, "rb") as fh:
            head = fh.read(8192)
        return hashlib.md5(head + str(size).encode()).hexdigest()
    except Exception:
        return ""


# ── SQLite cache helpers ──────────────────────────────────────────────────────
# Schema: two tables
#   metadata_cache  – fingerprint → DicomRecord JSON  (metadata pre-pass)
#   ai_cache        – fingerprint+anonymize → AI response JSON  (agent results)


def _get_db() -> sqlite3.Connection:
    """Open (and initialise) the SQLite cache database."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(CACHE_PATH), check_same_thread=False, timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute(
        "CREATE TABLE IF NOT EXISTS metadata_cache "
        "(fingerprint TEXT PRIMARY KEY, record_json TEXT NOT NULL)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS ai_cache "
        "(cache_key TEXT PRIMARY KEY, result_json TEXT NOT NULL)"
    )
    con.commit()
    _migrate_json_cache(con)
    return con


def _migrate_json_cache(con: sqlite3.Connection) -> None:
    """One-time migration: import legacy JSON cache into SQLite."""
    if not _LEGACY_JSON_CACHE.exists():
        return
    try:
        data = json.loads(_LEGACY_JSON_CACHE.read_text(encoding="utf-8"))
        rows = [(fp, json.dumps(rec, default=str)) for fp, rec in data.items()]
        con.executemany(
            "INSERT OR IGNORE INTO metadata_cache (fingerprint, record_json) VALUES (?, ?)",
            rows,
        )
        con.commit()
        _LEGACY_JSON_CACHE.rename(_LEGACY_JSON_CACHE.with_suffix(".json.migrated"))
        logger.info("Migrated %d records from legacy JSON cache to SQLite", len(rows))
    except Exception as exc:
        logger.warning("JSON cache migration failed (non-fatal): %s", exc)


def _load_cache() -> dict[str, dict]:
    """Load metadata cache from SQLite. Returns {fingerprint: record_dict}."""
    try:
        con = _get_db()
        rows = con.execute(
            "SELECT fingerprint, record_json FROM metadata_cache"
        ).fetchall()
        con.close()
        return {fp: json.loads(val) for fp, val in rows}
    except Exception as exc:
        logger.warning("Could not load metadata cache: %s", exc)
        return {}


def _save_cache(cache: dict[str, dict]) -> None:
    """Persist metadata cache records to SQLite (upsert)."""
    try:
        con = _get_db()
        rows = [(fp, json.dumps(rec, default=str)) for fp, rec in cache.items()]
        con.executemany(
            "INSERT OR REPLACE INTO metadata_cache (fingerprint, record_json) VALUES (?, ?)",
            rows,
        )
        con.commit()
        con.close()
    except Exception as exc:
        logger.warning("Could not save metadata cache: %s", exc)


def load_ai_cache_entry(fingerprint: str, anonymize: bool) -> dict | None:
    """Return cached AI result dict, or None if not cached."""
    key = f"{fingerprint}:{int(anonymize)}"
    try:
        con = _get_db()
        row = con.execute(
            "SELECT result_json FROM ai_cache WHERE cache_key = ?", (key,)
        ).fetchone()
        con.close()
        return json.loads(row[0]) if row else None
    except Exception:
        return None


def save_ai_cache_entry(fingerprint: str, anonymize: bool, result: dict) -> None:
    """Store AI result dict in cache."""
    key = f"{fingerprint}:{int(anonymize)}"
    try:
        con = _get_db()
        con.execute(
            "INSERT OR REPLACE INTO ai_cache (cache_key, result_json) VALUES (?, ?)",
            (key, json.dumps(result, default=str)),
        )
        con.commit()
        con.close()
    except Exception as exc:
        logger.warning("Could not save AI cache entry: %s", exc)


def clear_cache() -> None:
    """Delete the SQLite cache database entirely."""
    try:
        if CACHE_PATH.exists():
            CACHE_PATH.unlink()
        # Also remove WAL/SHM sidecar files if present
        for suffix in ("-wal", "-shm"):
            p = CACHE_PATH.with_suffix(".db" + suffix)
            if p.exists():
                p.unlink()
    except Exception as exc:
        logger.warning("Could not clear cache: %s", exc)


# ── Per-file workers (must be top-level for ProcessPoolExecutor pickling) ─────


def _worker_naive(path: str) -> dict:
    """Baseline worker: full file read including pixel data."""
    try:
        import pydicom  # imported inside worker so multiprocessing is safe

        ds = pydicom.dcmread(path)  # reads pixel data too
        return asdict(
            DicomRecord(
                file=path,
                patient_id=_safe_str(ds, "PatientID"),
                patient_name=_safe_str(ds, "PatientName"),
                patient_birthdate=_safe_str(ds, "PatientBirthDate"),
                patient_sex=_safe_str(ds, "PatientSex"),
                institution=_safe_str(ds, "InstitutionName"),
                study_date=_safe_str(ds, "StudyDate"),
                study_description=_safe_str(ds, "StudyDescription"),
                study_uid=_safe_str(ds, "StudyInstanceUID"),
                series_uid=_safe_str(ds, "SeriesInstanceUID"),
                sop_uid=_safe_str(ds, "SOPInstanceUID"),
                modality=_safe_str(ds, "Modality"),
                manufacturer=_safe_str(ds, "Manufacturer"),
                body_part=_safe_str(ds, "BodyPartExamined"),
                slice_thickness=_safe_str(ds, "SliceThickness"),
                pixel_spacing=_safe_str(ds, "PixelSpacing"),
                rows=_safe_int(ds, "Rows"),
                columns=_safe_int(ds, "Columns"),
                bits_allocated=_safe_int(ds, "BitsAllocated"),
            )
        )
    except Exception as exc:
        return asdict(DicomRecord(file=path, error=str(exc)))


def _worker_optimized(path: str) -> dict:
    """
    Optimized worker:
      • stop_before_pixels=True  – skip pixel data entirely
      • specific_tags             – parse only the tags we need
    """
    try:
        import pydicom

        ds = pydicom.dcmread(
            path,
            stop_before_pixels=True,
            specific_tags=ANALYSIS_TAGS,
        )
        return asdict(
            DicomRecord(
                file=path,
                patient_id=_safe_str(ds, "PatientID"),
                patient_name=_safe_str(ds, "PatientName"),
                patient_birthdate=_safe_str(ds, "PatientBirthDate"),
                patient_sex=_safe_str(ds, "PatientSex"),
                institution=_safe_str(ds, "InstitutionName"),
                study_date=_safe_str(ds, "StudyDate"),
                study_description=_safe_str(ds, "StudyDescription"),
                study_uid=_safe_str(ds, "StudyInstanceUID"),
                series_uid=_safe_str(ds, "SeriesInstanceUID"),
                sop_uid=_safe_str(ds, "SOPInstanceUID"),
                modality=_safe_str(ds, "Modality"),
                manufacturer=_safe_str(ds, "Manufacturer"),
                body_part=_safe_str(ds, "BodyPartExamined"),
                slice_thickness=_safe_str(ds, "SliceThickness"),
                pixel_spacing=_safe_str(ds, "PixelSpacing"),
                rows=_safe_int(ds, "Rows"),
                columns=_safe_int(ds, "Columns"),
                bits_allocated=_safe_int(ds, "BitsAllocated"),
            )
        )
    except Exception as exc:
        return asdict(DicomRecord(file=path, error=str(exc)))


# ── Public API ────────────────────────────────────────────────────────────────


def analyze_naive(paths: list[str]) -> BenchmarkResult:
    """
    Baseline sequential analyzer – mirrors what a naive implementation does.
    Reads every file fully (including pixel data) one by one.
    """
    t0 = time.perf_counter()
    records: list[DicomRecord] = []
    failed = 0

    for path in paths:
        rec = DicomRecord(**_worker_naive(path))
        if rec.error:
            failed += 1
        records.append(rec)

    elapsed = time.perf_counter() - t0
    return BenchmarkResult(
        records=records,
        elapsed_sec=round(elapsed, 3),
        total_files=len(paths),
        failed_files=failed,
        cache_hits=0,
        workers_used=1,
        strategy="naive",
    )


def analyze_optimized(
    paths: list[str],
    max_workers: int | None = None,
    use_cache: bool = True,
    chunk_size: int = 50,
) -> BenchmarkResult:
    """
    Optimized analyzer:
      1. File-hash cache – skip already-analyzed files
      2. stop_before_pixels + specific_tags – 10-50× faster per file
      3. ProcessPoolExecutor – parallel across CPU cores
      4. Chunked submission – keeps memory bounded for 1000+ files

    Parameters
    ----------
    paths       : list of absolute file paths to .dcm files
    max_workers : number of parallel workers (default: min(8, cpu_count))
    use_cache   : load/save results to data/dicom_opt_cache.json
    chunk_size  : submit files to executor in batches of this size
    """
    workers = max_workers or min(8, (os.cpu_count() or 4))
    # On Windows (spawn), pool creation costs ~0.5-2 s per run.
    # For very small batches, fall back to sequential to avoid negative speedup.
    if len(paths) < PARALLEL_THRESHOLD:
        workers = 1
    t0 = time.perf_counter()

    # ── Step 1: cache lookup ──────────────────────────────────────────────────
    cache: dict[str, dict] = _load_cache() if use_cache else {}
    to_process: list[tuple[str, str]] = []  # (path, fingerprint)
    cached_records: list[DicomRecord] = []
    cache_hits = 0

    for path in paths:
        fp = _file_fingerprint(path)
        if fp and fp in cache:
            rec = DicomRecord(**cache[fp])
            rec.from_cache = True
            cached_records.append(rec)
            cache_hits += 1
        else:
            to_process.append((path, fp))

    # ── Step 2: parallel processing of uncached files ─────────────────────────
    new_records: list[DicomRecord] = []
    failed = 0

    if to_process:
        uncached_paths = [p for p, _ in to_process]

        # Chunk into batches to bound memory for large sets
        all_futures: list = []
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for i in range(0, len(uncached_paths), chunk_size):
                batch = uncached_paths[i : i + chunk_size]
                for path in batch:
                    all_futures.append((executor.submit(_worker_optimized, path), path))

            fingerprint_map = {p: fp for p, fp in to_process}
            for future, path in all_futures:
                try:
                    raw = future.result()
                    rec = DicomRecord(**raw)
                    if rec.error:
                        failed += 1
                    else:
                        fp = fingerprint_map.get(path, "")
                        if fp and use_cache:
                            cache[fp] = asdict(rec)
                    new_records.append(rec)
                except Exception as exc:
                    new_records.append(DicomRecord(file=path, error=str(exc)))
                    failed += 1

    # ── Step 3: persist updated cache ────────────────────────────────────────
    if use_cache and new_records:
        _save_cache(cache)

    elapsed = time.perf_counter() - t0
    all_records = cached_records + new_records

    return BenchmarkResult(
        records=all_records,
        elapsed_sec=round(elapsed, 3),
        total_files=len(paths),
        failed_files=failed,
        cache_hits=cache_hits,
        workers_used=workers,
        strategy="optimized",
    )


# ── Benchmark summary helpers ─────────────────────────────────────────────────


def format_benchmark_table(naive: BenchmarkResult, optimized: BenchmarkResult) -> str:
    speedup = (
        round(naive.elapsed_sec / optimized.elapsed_sec, 1)
        if optimized.elapsed_sec > 0
        else "∞"
    )
    rows = [
        ("Files processed", naive.total_files, optimized.total_files),
        ("Elapsed (s)", naive.elapsed_sec, optimized.elapsed_sec),
        ("Throughput (files/s)", naive.throughput_fps, optimized.throughput_fps),
        ("Workers", naive.workers_used, optimized.workers_used),
        ("Cache hits", naive.cache_hits, optimized.cache_hits),
        ("Failed files", naive.failed_files, optimized.failed_files),
        ("Speed-up", "1×", f"{speedup}×"),
    ]
    col_w = 24
    header = f"{'Metric':<{col_w}} {'Naive':>12} {'Optimized':>12}"
    sep = "─" * len(header)
    lines = [sep, header, sep]
    for metric, n_val, o_val in rows:
        lines.append(f"{metric:<{col_w}} {str(n_val):>12} {str(o_val):>12}")
    lines.append(sep)
    return "\n".join(lines)


# ── Synthetic test-file generator (for demo when no real DICOMs available) ───


def generate_synthetic_dicoms(n: int = 20, target_dir: str | None = None) -> list[str]:
    """
    Create *n* minimal synthetic DICOM files for benchmarking.
    Uses pydicom's FileDataset API – no real patient data.
    Returns list of absolute paths.
    """
    try:
        import pydicom
        import pydicom.uid
        from pydicom.dataset import FileDataset, FileMetaDataset
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "pydicom (and numpy) are required. " "Run: pip install pydicom numpy"
        ) from exc

    out_dir = (
        Path(target_dir) if target_dir else Path(tempfile.mkdtemp(prefix="halo_dicom_"))
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []

    modalities = ["CT", "MR", "CR", "DX", "US", "NM", "PT"]
    manufacturers = ["Siemens", "GE", "Philips", "Canon", "Hologic"]

    for i in range(n):
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = pydicom.uid.CTImageStorage
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

        ds = FileDataset(
            filename_or_obj="",
            dataset={},
            file_meta=file_meta,
            is_implicit_VR=False,
            is_little_endian=True,
        )
        ds.is_implicit_VR = False
        ds.is_little_endian = True

        ds.PatientID = f"PAT{i:05d}"
        ds.PatientName = f"Test^Patient^{i}"
        ds.PatientBirthDate = f"{1950 + (i % 50):04d}0101"
        ds.PatientSex = "M" if i % 2 == 0 else "F"
        ds.InstitutionName = f"Hospital {chr(65 + i % 5)}"
        ds.StudyDate = f"202{3 + i % 2}0{1 + i % 9:02d}15"
        ds.StudyDescription = f"Synthetic study {i}"
        ds.StudyInstanceUID = pydicom.uid.generate_uid()
        ds.SeriesInstanceUID = pydicom.uid.generate_uid()
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = pydicom.uid.CTImageStorage
        ds.Modality = modalities[i % len(modalities)]
        ds.Manufacturer = manufacturers[i % len(manufacturers)]
        ds.BodyPartExamined = "CHEST"
        ds.SliceThickness = "1.5"
        ds.Rows = 512
        ds.Columns = 512
        ds.BitsAllocated = 16
        ds.BitsStored = 12
        ds.HighBit = 11
        ds.PixelRepresentation = 0
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"

        # Real pixel data so the naive reader actually has to work
        pixel_array = np.zeros((512, 512), dtype=np.int16)
        ds.PixelData = pixel_array.tobytes()

        path = out_dir / f"synthetic_{i:04d}.dcm"
        pydicom.dcmwrite(str(path), ds)
        paths.append(str(path))

    return paths
