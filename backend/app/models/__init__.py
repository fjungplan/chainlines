"""Database models package.

Ensure all model classes are imported so SQLAlchemy can register them,
avoiding lazy name resolution issues during mapper configuration.
"""

from app.models.team import TeamNode, TeamEra  # noqa: F401
from app.models.sponsor import (  # noqa: F401
	SponsorMaster,
	SponsorBrand,
	TeamSponsorLink,
)
from app.models.lineage import LineageEvent  # noqa: F401
from app.models.run_log import ScraperRun  # noqa: F401
from app.models.run_log import ScraperRun  # noqa: F401

__all__ = [
	"TeamNode",
	"TeamEra",
	"SponsorMaster",
	"SponsorBrand",
	"TeamSponsorLink",
	"LineageEvent",
    "ScraperRun",
]
