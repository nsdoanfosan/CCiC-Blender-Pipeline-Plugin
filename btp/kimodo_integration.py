# Copyright (C) 2026 PARK
#
# This file is part of a modified CC/iC-Blender-Pipeline-Plugin distribution
# and is licensed under the GNU General Public License version 3 or later.

"""Kimodo one-click target selection helpers for the official Data Link."""


REQUEST_TYPE = "KIMODO_TARGET"
AUTO_START_SERVICE = True


def selected_target_response(data_link):
    """Build a target reply and return the one selected iClone avatar."""
    actors = [actor for actor in data_link.get_selected_actors() if actor.is_avatar()]
    if len(actors) != 1:
        return ({
            "type": REQUEST_TYPE,
            "actors": [],
            "error": "Select exactly one avatar in iClone",
        }, [])

    actor = actors[0]
    return ({
        "type": REQUEST_TYPE,
        "actors": [{
            "name": actor.name,
            "type": actor.get_type(),
            "link_id": actor.get_link_id(),
        }],
    }, [actor])
