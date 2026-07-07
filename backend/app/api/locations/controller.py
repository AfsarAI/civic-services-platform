"""
Locations controller — public pincode and city lookup endpoints.
"""

from flask import request
from flask_restx import Namespace, Resource, fields

from app.api.locations.service import LocationService
from app.utils.responses import error_response, success_response

ns = Namespace("locations", description="Location lookup operations", path="/locations")
_svc = LocationService()

_envelope = ns.model(
    "LocationEnvelope",
    {
        "success": fields.Boolean,
        "message": fields.String,
        "data": fields.Raw,
        "errors": fields.Raw,
    },
)


@ns.route("/pincode/<string:pincode>")
@ns.param("pincode", "6-digit postal code")
class PincodeLookupResource(Resource):
    @ns.response(200, "Pincode lookup result", _envelope)
    @ns.response(400, "Invalid pincode", _envelope)
    def get(self, pincode):
        """Resolve one pincode into one or more city options."""
        normalized = (pincode or "").strip()
        if len(normalized) != 6 or not normalized.isdigit():
            return error_response("Pincode must be exactly 6 digits.", status_code=400)

        data = _svc.lookup_pincode(normalized)
        if data["match_count"] == 0:
            return success_response(data, "No city mappings found for this pincode.")
        if data["match_count"] == 1:
            return success_response(data, "Pincode resolved to a single city.")
        return success_response(data, "Multiple city options found for this pincode.")


@ns.route("/cities")
class CitySearchResource(Resource):
    @ns.response(200, "City suggestion list", _envelope)
    def get(self):
        """Search active cities by name for autosuggest UI components."""
        query = request.args.get("query", default="", type=str)
        limit = request.args.get("limit", default=10, type=int)
        data = _svc.search_cities(query=query, limit=limit)
        return success_response(data, "Cities retrieved.")


@ns.route("/pincodes")
class PincodePrefixSearchResource(Resource):
    @ns.response(200, "Pincode suggestions", _envelope)
    def get(self):
        """Autocomplete pincode suggestions after user types at least 2 digits."""
        prefix = request.args.get("prefix", default="", type=str)
        limit = request.args.get("limit", default=10, type=int)

        data = _svc.search_pincode_prefix(prefix=prefix, limit=limit)
        if len((prefix or "").strip()) < 2:
            return success_response(data, "Type at least 2 digits to see pincode suggestions.")
        if data["count"] == 0:
            return success_response(data, "No matching pincode suggestions found.")
        return success_response(data, "Pincode suggestions retrieved.")


@ns.route("/reverse-geocode")
class ReverseGeocodeResource(Resource):
    @ns.response(200, "Reverse geocode lookup", _envelope)
    @ns.response(400, "Invalid coordinates", _envelope)
    def get(self):
        """Resolve map coordinates into address, pincode and city options."""
        latitude = request.args.get("lat", type=float)
        longitude = request.args.get("lon", type=float)

        if latitude is None or longitude is None:
            return error_response("lat and lon query parameters are required.", status_code=400)

        try:
            data = _svc.reverse_geocode(latitude=latitude, longitude=longitude)
            return success_response(data, "Location resolved from coordinates.")
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/overview")
class PublicOverviewResource(Resource):
    @ns.response(200, "Public platform overview", _envelope)
    def get(self):
        """Public summary for landing page metrics."""
        data = _svc.get_public_overview()
        return success_response(data, "Platform overview retrieved.")


@ns.route("/complaint-pins")
class PublicComplaintPinsResource(Resource):
    @ns.response(200, "Public complaint map markers", _envelope)
    def get(self):
        """Public complaint map pins based on stored coordinates."""
        limit = request.args.get("limit", default=500, type=int)
        data = _svc.get_public_complaint_pins(limit=limit)
        if data["count"] == 0:
            return success_response(data, "No complaint coordinates available yet.")
        return success_response(data, "Complaint map markers retrieved.")
