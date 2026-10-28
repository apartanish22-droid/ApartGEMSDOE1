"""Compatibility access to the shared literal registry gate.

The old sampled-rank/blanket-exemption implementation could clear duplicates.
It is deliberately unavailable: callers must use the full shared inventory gate.
"""
from gems57.uniqueness import compare_array_to_registry


def _compare(candidate, footprint, registry_index, **kwargs):
    if registry_index is None:
        raise RuntimeError('Full registry index required; the old sampled index cannot clear a lane')
    return compare_array_to_registry(candidate, registry_index, footprint, **kwargs)


def check_surface_uniqueness(surface, footprint, *, registry_index=None, **kwargs):
    return _compare(surface, footprint, registry_index, **kwargs)


def check_final_raster_uniqueness(final_raster, footprint, *, registry_index=None, **kwargs):
    return _compare(final_raster, footprint, registry_index, **kwargs)
