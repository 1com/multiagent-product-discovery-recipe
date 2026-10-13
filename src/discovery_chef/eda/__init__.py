"""Phase 1: exploratory data analysis of the PantryPal research data."""

from discovery_chef.eda.profile import (
    EdaProfile,
    build_profile,
    findings_markdown,
    run_eda,
    write_outputs,
)

__all__ = ["EdaProfile", "build_profile", "findings_markdown", "run_eda", "write_outputs"]
