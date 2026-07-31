# Copyright (C) 2026 PARK
#
# This file is part of a modified CC/iC-Blender-Pipeline-Plugin distribution
# and is licensed under the GNU General Public License version 3 or later.

"""Kimodo project catalog and exact-target helpers for the official Data Link."""

from __future__ import annotations

import hashlib
import os

from RLPy import RApplication


CATALOG_REQUEST_TYPE = "KIMODO_CATALOG"
TARGET_REQUEST_TYPE = "KIMODO_TARGET"
AUTO_START_SERVICE = True
_PROJECTS_WITH_NEW_LINK_IDS = set()


def _normal_path(path):
    return os.path.normcase(os.path.normpath(str(path or "")))


def project_identity():
    """Describe the current project without saving or changing it."""
    current_path = str(RApplication.GetCurrentProjectPath() or "")
    default_path = str(RApplication.GetDefaultProjectPath() or "")
    normalized_path = _normal_path(current_path)
    is_default = bool(normalized_path and normalized_path == _normal_path(default_path))
    session_only = not normalized_path or is_default
    digest = hashlib.sha256(normalized_path.encode("utf-8")).hexdigest()[:24]
    if session_only:
        project_key = "session:{}:{}".format(os.getpid(), digest or "unsaved")
    else:
        project_key = "path:{}".format(digest)
    return {
        "key": project_key,
        "path": current_path,
        "name": os.path.basename(current_path) if current_path else "Unsaved iClone Project",
        "saved": not session_only,
        "is_default": is_default,
        "session_only": session_only,
    }


def _avatar_entries(data_link):
    entries = []
    actors = data_link.get_avatar_actors()
    for actor in actors:
        entries.append({
            "name": actor.name,
            "type": actor.get_type(),
            "link_id": actor.get_link_id(),
            "link_id_was_new": bool(getattr(actor, "kimodo_link_id_was_new", False)),
        })
    return entries, actors


def catalog_response(data_link):
    """Return every avatar in the current iClone project."""
    project = project_identity()
    entries, _actors = _avatar_entries(data_link)
    if any(item["link_id_was_new"] for item in entries):
        _PROJECTS_WITH_NEW_LINK_IDS.add(project["key"])
    return {
        "type": CATALOG_REQUEST_TYPE,
        "project": project,
        "actors": entries,
        "project_needs_save": project["key"] in _PROJECTS_WITH_NEW_LINK_IDS,
    }


def exact_target_response(data_link, request):
    """Resolve one avatar by Link ID, independent of the iClone selection."""
    project = project_identity()
    requested_project = str(request.get("project_key") or "")
    requested_link_id = str(request.get("link_id") or "")
    base = {
        "type": TARGET_REQUEST_TYPE,
        "project": project,
        "actors": [],
    }
    if not requested_project or requested_project != project["key"]:
        base.update({
            "error": "The iClone project changed. Refresh the avatar list and try again.",
            "error_code": "PROJECT_CHANGED",
        })
        return base, []
    if not requested_link_id:
        base.update({
            "error": "No iClone target was registered. Choose an avatar in Blender.",
            "error_code": "TARGET_REQUIRED",
        })
        return base, []

    _entries, actors = _avatar_entries(data_link)
    matches = [actor for actor in actors if actor.get_link_id() == requested_link_id]
    if len(matches) != 1:
        base.update({
            "error": "The registered iClone avatar is no longer available. Refresh and choose a target again.",
            "error_code": "TARGET_NOT_FOUND",
        })
        return base, []

    actor = matches[0]
    base["actors"] = [{
        "name": actor.name,
        "type": actor.get_type(),
        "link_id": actor.get_link_id(),
    }]
    return base, [actor]
