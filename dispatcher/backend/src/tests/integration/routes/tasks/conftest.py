from bson import ObjectId
import pytest

def make_schedule(id: ObjectId, name: str):
    nonlocal schedule_id = None

    def _make_schedule():
        return {

        }