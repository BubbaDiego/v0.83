# core/logging.py

import sys
import os
from utils.rich_logger import RichLogger

log = RichLogger()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def configure_console_log():
    """🧠 Cyclone Logging Configuration"""
    log.hijack_logger("werkzeug")
    # log.silence_module("werkzeug")
    # log.silence_module("fuzzy_wuzzy")
    # log.silence_module("flask")
    log.silence_module("calc_services")

    log.assign_group(
        "cyclone_core",
        [
            "cyclone_engine",
            "Cyclone",
            "CycloneHedgeService",
            "CyclonePortfolioService",
            "CycloneAlertService",
            "CyclonePositionService",
        ],
    )
    log.enable_group("cyclone_core")

    # Silence DataLocker and related DL manager modules during init
    for module in [
        "DataLocker",
        "DLAlertManager",
        "DLPriceManager",
        "DLPositionManager",
        "DLWalletManager",
        "DLBrokerManager",
        "DLPortfolioManager",
        "DLSystemDataManager",
        "DLMonitorLedger",
        "DLModifierManager",
        "DLThresholdManager",
    ]:
        log.silence_module(module)
    log.init_status()
