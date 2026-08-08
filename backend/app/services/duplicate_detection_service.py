"""
Duplicate detection service — finds nearby open complaints that might be
reports of the same physical issue (e.g. the same pothole), shared by both
the citizen submission flow (advisory warning) and the administrator review
flow (manual "mark as duplicate" action).
"""

from app.models.complaint import Complaint
from app.services.system_settings_service import SystemSettingsService
from app.utils.geo import bounding_box_deltas, haversine_distance_meters

# Only complaints still "open" are worth flagging — no point comparing
# against ones already resolved, closed, rejected, or cancelled.
OPEN_STATUSES = (
    Complaint.STATUS_PENDING,
    Complaint.STATUS_ASSIGNED,
    Complaint.STATUS_IN_PROGRESS,
)


class DuplicateDetectionService:
    """Finds candidate duplicate complaints near a given location."""

    @staticmethod
    def default_radius_meters() -> int:
        return SystemSettingsService.duplicate_detection_radius_meters()

    @staticmethod
    def find_nearby_open_complaints(
        latitude: float,
        longitude: float,
        radius_meters: int = None,
        exclude_complaint_id: int = None,
        city_id: int = None,
    ) -> list[tuple[float, Complaint]]:
        """Return ``(distance_meters, Complaint)`` pairs within ``radius_meters``,
        nearest first.

        Only considers complaints that are still open and not already linked
        as a duplicate of something else (no duplicate-of-duplicate chains).
        """
        radius = radius_meters or DuplicateDetectionService.default_radius_meters()
        lat_delta, lon_delta = bounding_box_deltas(latitude, radius)

        query = Complaint.query.filter(
            Complaint.status.in_(OPEN_STATUSES),
            Complaint.duplicate_of_id.is_(None),
            Complaint.latitude.isnot(None),
            Complaint.longitude.isnot(None),
            Complaint.latitude.between(latitude - lat_delta, latitude + lat_delta),
            Complaint.longitude.between(longitude - lon_delta, longitude + lon_delta),
        )
        if exclude_complaint_id is not None:
            query = query.filter(Complaint.id != exclude_complaint_id)
        if city_id is not None:
            query = query.filter(Complaint.city_id == city_id)

        candidates = []
        for complaint in query.all():
            distance = haversine_distance_meters(
                latitude, longitude, complaint.latitude, complaint.longitude
            )
            if distance <= radius:
                candidates.append((distance, complaint))

        candidates.sort(key=lambda pair: pair[0])
        return candidates
