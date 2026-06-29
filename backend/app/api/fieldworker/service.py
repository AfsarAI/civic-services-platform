"""
Field Worker service — business logic placeholder.
"""


class FieldWorkerService:
    """Handles field-worker-facing business operations."""

    def get_assignments(self, worker_id: int, page: int, per_page: int) -> dict:
        """Retrieve assigned tasks for a worker. TODO: implement."""
        raise NotImplementedError

    def get_assignment(self, assignment_id: int, worker_id: int) -> dict:
        """Retrieve a specific assignment. TODO: implement."""
        raise NotImplementedError

    def update_progress(self, assignment_id: int, worker_id: int, data: dict) -> dict:
        """Update repair progress. TODO: implement."""
        raise NotImplementedError

    def accept_assignment(self, assignment_id: int, worker_id: int) -> dict:
        """Accept an assigned task. TODO: implement."""
        raise NotImplementedError

    def complete_assignment(self, assignment_id: int, worker_id: int) -> dict:
        """Mark task as completed. TODO: implement."""
        raise NotImplementedError

    def get_dashboard_summary(self, worker_id: int) -> dict:
        """Return dashboard statistics. TODO: implement."""
        raise NotImplementedError
