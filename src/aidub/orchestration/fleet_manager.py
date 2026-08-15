"""
Worker Fleet Health & VRAM Load-Balancer.

Supervises worker node heartbeats, monitors VRAM utilization, and manages dynamic auto-failover.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from aidub.orchestration.cluster_scheduler import ClusterWorkerNode

logger = logging.getLogger(__name__)


class FleetManager:
    """
    Supervises fleet health and auto-failover.
    """

    def audit_fleet_health(self, nodes: Sequence[ClusterWorkerNode]) -> dict[str, str]:
        """
        Audit health status across cluster fleet.
        """
        status_map = {}
        for n in nodes:
            st = "HEALTHY" if n.available_vram_gb > 2.0 else "VRAM_WARNING"
            status_map[str(n.node_id)] = st

        logger.info("fleet_manager: audited %d worker nodes in fleet", len(nodes))
        return status_map


__all__ = [
    "FleetManager",
]
