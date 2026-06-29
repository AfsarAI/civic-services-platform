"""
Citizen service — business logic placeholder.
"""


class CitizenService:
    """Handles citizen-facing business operations."""

    def get_my_complaints(self, citizen_id: int, page: int, per_page: int) -> dict:
        """Retrieve paginated complaints for a citizen. TODO: implement."""
        raise NotImplementedError

    def submit_complaint(self, citizen_id: int, data: dict) -> dict:
        """Create a new complaint. TODO: implement."""
        raise NotImplementedError

    def get_complaint(self, complaint_id: int, citizen_id: int) -> dict:
        """Retrieve a specific complaint owned by the citizen. TODO: implement."""
        raise NotImplementedError

    def update_complaint(self, complaint_id: int, citizen_id: int, data: dict) -> dict:
        """Update a pending complaint. TODO: implement."""
        raise NotImplementedError

    def delete_complaint(self, complaint_id: int, citizen_id: int) -> None:
        """Delete a pending complaint. TODO: implement."""
        raise NotImplementedError

    def submit_feedback(self, complaint_id: int, citizen_id: int, data: dict) -> dict:
        """Submit feedback for a resolved complaint. TODO: implement."""
        raise NotImplementedError

    def get_dashboard_summary(self, citizen_id: int) -> dict:
        """Return dashboard statistics. TODO: implement."""
        raise NotImplementedError
