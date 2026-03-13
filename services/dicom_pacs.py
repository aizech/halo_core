"""DICOM PACS integration for querying and retrieving studies.

Provides functions to query PACS servers using DICOM C-FIND and
retrieve studies using C-MOVE operations.
"""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.settings import get_settings

_logger = logging.getLogger(__name__)

# pynetdicom is optional
try:
    from pynetdicom import AE, QueryRetrievePresentationContexts
    from pynetdicom.sop_class import (
        StudyRootQueryRetrieveInformationModelFind,
        StudyRootQueryRetrieveInformationModelMove,
    )
    from pydicom.dataset import Dataset

    PACS_AVAILABLE = True
except ImportError:
    PACS_AVAILABLE = False
    _logger.debug("pynetdicom not available - PACS integration disabled")


def is_pacs_available() -> bool:
    """Check if PACS integration is available."""
    return PACS_AVAILABLE


@dataclass
class PACSConfig:
    """PACS server configuration."""

    host: str
    port: int
    calling_ae: str  # Our AE title
    called_ae: str  # PACS AE title
    timeout: int = 30

    @classmethod
    def from_settings(cls) -> Optional["PACSConfig"]:
        """Create PACSConfig from settings."""
        settings = get_settings()

        if not all(
            [
                settings.dicom_pacs_host,
                settings.dicom_pacs_port,
                settings.dicom_pacs_ae_title,
            ]
        ):
            return None

        return cls(
            host=settings.dicom_pacs_host,
            port=settings.dicom_pacs_port,
            calling_ae="HALO_CORE",  # Our AE title
            called_ae=settings.dicom_pacs_ae_title,
            timeout=30,
        )


@dataclass
class PACSStudy:
    """Represents a study found on PACS."""

    patient_id: str
    patient_name: str
    study_instance_uid: str
    study_date: str
    study_description: str
    modality: str
    study_id: str
    accession_number: str
    number_of_series: int = 0
    number_of_images: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "study_instance_uid": self.study_instance_uid,
            "study_date": self.study_date,
            "study_description": self.study_description,
            "modality": self.modality,
            "study_id": self.study_id,
            "accession_number": self.accession_number,
            "number_of_series": self.number_of_series,
            "number_of_images": self.number_of_images,
        }


@dataclass
class PACSSeries:
    """Represents a series within a PACS study."""

    series_instance_uid: str
    series_number: int
    series_description: str
    modality: str
    number_of_images: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "series_instance_uid": self.series_instance_uid,
            "series_number": self.series_number,
            "series_description": self.series_description,
            "modality": self.modality,
            "number_of_images": self.number_of_images,
        }


@dataclass
class PACSQueryResult:
    """Result of a PACS query operation."""

    success: bool
    studies: List[PACSStudy] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "studies": [s.to_dict() for s in self.studies],
            "error": self.error,
        }


@dataclass
class PACSRetrieveResult:
    """Result of a PACS retrieve operation."""

    success: bool
    study_instance_uid: str
    output_directory: Optional[Path] = None
    files_retrieved: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "study_instance_uid": self.study_instance_uid,
            "output_directory": (
                str(self.output_directory) if self.output_directory else None
            ),
            "files_retrieved": self.files_retrieved,
            "error": self.error,
        }


def query_studies(
    patient_id: Optional[str] = None,
    patient_name: Optional[str] = None,
    study_date: Optional[date] = None,
    modality: Optional[str] = None,
    study_description: Optional[str] = None,
    config: Optional[PACSConfig] = None,
) -> PACSQueryResult:
    """Query PACS for studies matching criteria.

    Args:
        patient_id: Patient ID filter
        patient_name: Patient name filter (wildcards supported)
        study_date: Study date filter
        modality: Modality filter (CT, MR, US, etc.)
        study_description: Study description filter
        config: PACS configuration (uses settings if not provided)

    Returns:
        PACSQueryResult with matching studies
    """
    if not PACS_AVAILABLE:
        return PACSQueryResult(
            success=False,
            error="pynetdicom not installed - PACS integration unavailable",
        )

    if config is None:
        config = PACSConfig.from_settings()

    if config is None:
        return PACSQueryResult(
            success=False,
            error="PACS not configured - set DICOM_PACS_HOST, DICOM_PACS_PORT, DICOM_PACS_AE_TITLE",
        )

    try:
        # Create Application Entity
        ae = AE(ae_title=config.calling_ae)

        # Add presentation contexts for Query/Retrieve
        ae.supported_contexts = QueryRetrievePresentationContexts

        # Build query dataset
        query = Dataset()
        query.QueryRetrieveLevel = "STUDY"

        # Set query keys
        if patient_id:
            query.PatientID = patient_id
        if patient_name:
            query.PatientName = patient_name
        if study_date:
            query.StudyDate = study_date.strftime("%Y%m%d")
        if modality:
            query.Modality = modality
        if study_description:
            query.StudyDescription = study_description

        # Requested keys (what we want back)
        query.PatientID = query.get("PatientID", "")
        query.PatientName = query.get("PatientName", "")
        query.StudyInstanceUID = ""
        query.StudyDate = query.get("StudyDate", "")
        query.StudyDescription = ""
        query.Modality = query.get("Modality", "")
        query.StudyID = ""
        query.AccessionNumber = ""
        query.NumberOfStudyRelatedSeries = ""
        query.NumberOfStudyRelatedInstances = ""

        studies: List[PACSStudy] = []

        # Associate with PACS
        assoc = ae.associate(config.host, config.port, ae_title=config.called_ae)

        if assoc.is_established:
            # Send C-FIND
            responses = assoc.send_c_find(
                query,
                query_model=StudyRootQueryRetrieveInformationModelFind,
            )

            for status, ds in responses:
                if status and ds:
                    study = PACSStudy(
                        patient_id=str(getattr(ds, "PatientID", "")),
                        patient_name=str(getattr(ds, "PatientName", "")),
                        study_instance_uid=str(getattr(ds, "StudyInstanceUID", "")),
                        study_date=str(getattr(ds, "StudyDate", "")),
                        study_description=str(getattr(ds, "StudyDescription", "")),
                        modality=str(getattr(ds, "Modality", "")),
                        study_id=str(getattr(ds, "StudyID", "")),
                        accession_number=str(getattr(ds, "AccessionNumber", "")),
                        number_of_series=int(
                            getattr(ds, "NumberOfStudyRelatedSeries", 0)
                        ),
                        number_of_images=int(
                            getattr(ds, "NumberOfStudyRelatedInstances", 0)
                        ),
                    )
                    studies.append(study)

            assoc.release()

            return PACSQueryResult(success=True, studies=studies)

        else:
            return PACSQueryResult(
                success=False,
                error=f"Failed to associate with PACS at {config.host}:{config.port}",
            )

    except Exception as e:
        _logger.error("PACS query failed: %s", e)
        return PACSQueryResult(success=False, error=str(e))


def query_series(
    study_instance_uid: str,
    config: Optional[PACSConfig] = None,
) -> List[PACSSeries]:
    """Query PACS for series within a study.

    Args:
        study_instance_uid: Study Instance UID to query
        config: PACS configuration

    Returns:
        List of PACSSeries objects
    """
    if not PACS_AVAILABLE:
        _logger.warning("pynetdicom not installed")
        return []

    if config is None:
        config = PACSConfig.from_settings()

    if config is None:
        _logger.warning("PACS not configured")
        return []

    try:
        ae = AE(ae_title=config.calling_ae)
        ae.supported_contexts = QueryRetrievePresentationContexts

        # Build query for SERIES level
        query = Dataset()
        query.QueryRetrieveLevel = "SERIES"
        query.StudyInstanceUID = study_instance_uid

        # Requested keys
        query.SeriesInstanceUID = ""
        query.SeriesNumber = ""
        query.SeriesDescription = ""
        query.Modality = ""
        query.NumberOfSeriesRelatedInstances = ""

        series_list: List[PACSSeries] = []

        assoc = ae.associate(config.host, config.port, ae_title=config.called_ae)

        if assoc.is_established:
            responses = assoc.send_c_find(
                query,
                query_model=StudyRootQueryRetrieveInformationModelFind,
            )

            for status, ds in responses:
                if status and ds:
                    series = PACSSeries(
                        series_instance_uid=str(getattr(ds, "SeriesInstanceUID", "")),
                        series_number=int(getattr(ds, "SeriesNumber", 0)),
                        series_description=str(getattr(ds, "SeriesDescription", "")),
                        modality=str(getattr(ds, "Modality", "")),
                        number_of_images=int(
                            getattr(ds, "NumberOfSeriesRelatedInstances", 0)
                        ),
                    )
                    series_list.append(series)

            assoc.release()

        return series_list

    except Exception as e:
        _logger.error("PACS series query failed: %s", e)
        return []


def retrieve_study(
    study_instance_uid: str,
    output_dir: Optional[Path] = None,
    config: Optional[PACSConfig] = None,
    progress_callback: Optional[callable] = None,
) -> PACSRetrieveResult:
    """Retrieve a study from PACS using C-MOVE.

    Note: C-MOVE requires a DICOM Storage SCP to be running to receive
    the images. This implementation sets up a temporary SCP.

    Args:
        study_instance_uid: Study Instance UID to retrieve
        output_dir: Directory to save retrieved files
        config: PACS configuration
        progress_callback: Optional callback for progress updates

    Returns:
        PACSRetrieveResult with retrieval status
    """
    if not PACS_AVAILABLE:
        return PACSRetrieveResult(
            success=False,
            study_instance_uid=study_instance_uid,
            error="pynetdicom not installed",
        )

    if config is None:
        config = PACSConfig.from_settings()

    if config is None:
        return PACSRetrieveResult(
            success=False,
            study_instance_uid=study_instance_uid,
            error="PACS not configured",
        )

    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="pacs_retrieve_"))
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create a Storage SCP to receive images
        from pynetdicom import AllStoragePresentationContexts

        ae = AE(ae_title=config.calling_ae)
        ae.supported_contexts = AllStoragePresentationContexts

        # Track received files
        received_files: List[Path] = []

        def handle_store(event):
            """Handle incoming C-STORE requests."""
            ds = event.dataset
            sop_uid = getattr(ds, "SOPInstanceUID", "unknown")
            filename = output_dir / f"{sop_uid}.dcm"
            ds.save_as(filename, write_like_original=False)
            received_files.append(filename)

            if progress_callback:
                progress_callback(len(received_files), sop_uid)

            return 0x0000  # Success

        ae.on_c_store = handle_store

        # Start SCP in background
        scp = ae.start_server(("", 0), block=False)

        try:
            # Request C-MOVE to send to our SCP
            assoc = ae.associate(config.host, config.port, ae_title=config.called_ae)

            if assoc.is_established:
                # Build move request
                query = Dataset()
                query.QueryRetrieveLevel = "STUDY"
                query.StudyInstanceUID = study_instance_uid

                # Send C-MOVE to our SCP
                responses = assoc.send_c_move(
                    query,
                    config.calling_ae,  # Move destination (our AE)
                    query_model=StudyRootQueryRetrieveInformationModelMove,
                )

                for status, _ in responses:
                    if status and status.Status == 0x0000:
                        # Success
                        pass

                assoc.release()

            # Wait a bit for any remaining transfers
            import time

            time.sleep(2)

        finally:
            scp.shutdown()

        return PACSRetrieveResult(
            success=True,
            study_instance_uid=study_instance_uid,
            output_directory=output_dir,
            files_retrieved=len(received_files),
        )

    except Exception as e:
        _logger.error("PACS retrieve failed: %s", e)
        return PACSRetrieveResult(
            success=False,
            study_instance_uid=study_instance_uid,
            error=str(e),
        )


def retrieve_series(
    study_instance_uid: str,
    series_instance_uid: str,
    output_dir: Optional[Path] = None,
    config: Optional[PACSConfig] = None,
    progress_callback: Optional[callable] = None,
) -> PACSRetrieveResult:
    """Retrieve a specific series from PACS.

    Args:
        study_instance_uid: Study Instance UID
        series_instance_uid: Series Instance UID to retrieve
        output_dir: Directory to save retrieved files
        config: PACS configuration
        progress_callback: Optional callback for progress updates

    Returns:
        PACSRetrieveResult with retrieval status
    """
    if not PACS_AVAILABLE:
        return PACSRetrieveResult(
            success=False,
            study_instance_uid=study_instance_uid,
            error="pynetdicom not installed",
        )

    if config is None:
        config = PACSConfig.from_settings()

    if config is None:
        return PACSRetrieveResult(
            success=False,
            study_instance_uid=study_instance_uid,
            error="PACS not configured",
        )

    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="pacs_series_"))
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        from pynetdicom import AllStoragePresentationContexts

        ae = AE(ae_title=config.calling_ae)
        ae.supported_contexts = AllStoragePresentationContexts

        received_files: List[Path] = []

        def handle_store(event):
            ds = event.dataset
            sop_uid = getattr(ds, "SOPInstanceUID", "unknown")
            filename = output_dir / f"{sop_uid}.dcm"
            ds.save_as(filename, write_like_original=False)
            received_files.append(filename)

            if progress_callback:
                progress_callback(len(received_files), sop_uid)

            return 0x0000

        ae.on_c_store = handle_store

        scp = ae.start_server(("", 0), block=False)

        try:
            assoc = ae.associate(config.host, config.port, ae_title=config.called_ae)

            if assoc.is_established:
                query = Dataset()
                query.QueryRetrieveLevel = "SERIES"
                query.StudyInstanceUID = study_instance_uid
                query.SeriesInstanceUID = series_instance_uid

                responses = assoc.send_c_move(
                    query,
                    config.calling_ae,
                    query_model=StudyRootQueryRetrieveInformationModelMove,
                )

                for status, _ in responses:
                    pass

                assoc.release()

            import time

            time.sleep(1)

        finally:
            scp.shutdown()

        return PACSRetrieveResult(
            success=True,
            study_instance_uid=study_instance_uid,
            output_directory=output_dir,
            files_retrieved=len(received_files),
        )

    except Exception as e:
        _logger.error("PACS series retrieve failed: %s", e)
        return PACSRetrieveResult(
            success=False,
            study_instance_uid=study_instance_uid,
            error=str(e),
        )


def test_pacs_connection(config: Optional[PACSConfig] = None) -> Tuple[bool, str]:
    """Test PACS server connection.

    Args:
        config: PACS configuration

    Returns:
        Tuple of (success, message)
    """

    if not PACS_AVAILABLE:
        return False, "pynetdicom not installed"

    if config is None:
        config = PACSConfig.from_settings()

    if config is None:
        return False, "PACS not configured"

    try:
        ae = AE(ae_title=config.calling_ae)
        ae.supported_contexts = QueryRetrievePresentationContexts

        # Try to associate
        assoc = ae.associate(config.host, config.port, ae_title=config.called_ae)

        if assoc.is_established:
            assoc.release()
            return (
                True,
                f"Successfully connected to PACS at {config.host}:{config.port}",
            )
        else:
            return (
                False,
                f"Failed to establish association with {config.host}:{config.port}",
            )

    except Exception as e:
        return False, f"Connection error: {e}"
