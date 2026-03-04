"""Module for transferring data from hard drive to NAS after a flight.
Supports multiple flight folders since trajectory matching is already complete.
"""
import logging
from pathlib import Path
from code.file_utils import check_drive_mounted
from code.tools.postflightdtt.postflightdtt_helpers import (
    get_resolved_config,
    backup_source,
    transfer_data,
    cleanup_source
)


logger = logging.getLogger(__name__)


def hd_to_nas_transfer(config: dict) -> None:
    """Load config and transfer data from hard drive to NAS."""
    logger.info("Starting Hard Drive to NAS Transfer")
    # Abort if NAS not mounted
    check_drive_mounted(
        path=Path(config['file_transfer']['hd_to_nas']['destination_path']))
    # Load Resolve Config
    resolved_config = get_resolved_config(config=config)
    # Processing Steps
    transfer_harddisk_data(config=resolved_config)


def transfer_harddisk_data(config) -> None:
    """ Transfer recordings data from hard drive to NAS, with cleanup after transfer.
    Backup before transfer is possible if enabled in config."""
    source_path = config['file_transfer']['hd_to_nas']['source_path']
    destination_path = config['file_transfer']['hd_to_nas']['destination_path']
    # Backup before transfer if enabled in config
    backup = config['file_transfer']['hd_to_nas']['backup']
    if backup:
        backup_path = config['file_transfer']['hd_to_nas']['backup_path']
        backup_source(src_path=source_path, dst_path=backup_path)
    # Transfer data
    logger.info("Transferring Hard Disk data to NAS...")
    transfer_data(src_path=source_path, dst_path=destination_path)
    # Cleanup
    cleanup_source(src_path=source_path)
    source_path.mkdir()  # Recreate empty recordings folder after transfer
