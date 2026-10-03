"""Initial-2024 legal rule candidates; never an official individual assignment path.

All densities must use the frozen INSEE production geography and municipal
population. Defaults are independently reconstructed 2020/COG2023 medians;
their two-decimal displays match the contemporary official thresholds.
None and numeric NaN are unknown, never automatically ineligible.
"""
from math import isfinite
from typing import Optional

Tri = Optional[bool]
RECONSTRUCTED_CUTOFFS = dict(epci_density=63.569845464551264, epci_income=21570.0,
                        mountain_income=22822.5, bassin_density=70.84363836218742,
                        bassin_income=21600.0, department_density=35.0,
                        department_income=21665.0, commune_population=30000)


def _missing(value):
    if value is None:
        return True
    try:
        return not isfinite(value)
    except TypeError:
        return False


def _state(value) -> Tri:
    return None if _missing(value) else bool(value)


def _and(*values: Tri) -> Tri:
    states = [_state(value) for value in values]
    if any(value is False for value in states):
        return False
    return None if any(value is None for value in states) else True


def _le(value, cutoff) -> Tri:
    return None if _missing(value) else bool(value <= cutoff)


def _lt(value, cutoff) -> Tri:
    return None if _missing(value) else bool(value < cutoff)


def candidate_routes(row, cutoffs=None):
    """Return tri-state candidates without consulting observed treatment.

    Required keys: metro, commune_pop2020_municipal, epci_fp_member,
    isolated_L5210_1_1V, epci_density, epci_med20, commune_density,
    commune_med20, bv_density, bv_med20, department_density,
    department_med20, epci_mountain_population_share,
    guyane, reunion_in_zsar.
    Missing keys are unknown. B includes only numerical conditions; actual B
    additionally requires a regional-prefect proposal and ministerial acceptance.
    """
    c = {**RECONSTRUCTED_CUTOFFS, **(cutoffs or {})}
    common = _and(row.get('metro'), _lt(row.get('commune_pop2020_municipal'), c['commune_population']))
    epci = _and(common, row.get('epci_fp_member'))
    mountain = row.get('epci_mountain_population_share')
    return dict(
        A_epci=_and(epci, _le(row.get('epci_density'), c['epci_density']), _le(row.get('epci_med20'), c['epci_income'])),
        A_isolated=_and(common, row.get('isolated_L5210_1_1V'), _le(row.get('commune_density'), c['epci_density']), _le(row.get('commune_med20'), c['epci_income'])),
        B_numerically_possible=_and(common, _le(row.get('bv_density'), c['bassin_density']), _le(row.get('bv_med20'), c['bassin_income'])),
        C_department=_and(common, _lt(row.get('department_density'), c['department_density']), _le(row.get('department_med20'), c['department_income'])),
        D_mountain=_and(epci, None if _missing(mountain) else bool(mountain >= .5), _le(row.get('epci_density'), c['epci_density']), _le(row.get('epci_med20'), c['mountain_income'])),
        E_overseas=True if _state(row.get('guyane')) is True or _state(row.get('reunion_in_zsar')) is True else (False if _state(row.get('guyane')) is False and _state(row.get('reunion_in_zsar')) is False else None),
    )


def density_domain_candidate(row, cutoffs=None):
    """Conservative commune-domain inclusion; EPCI aggregation needs a further
    whole-EPCI membership check. Geography validity must be documented upstream.
    Mountain D is redundant with A when epci_med20 <= the ordinary threshold.
    Reproduced cutoffs do not certify original administrative path records.
    """
    c = {**RECONSTRUCTED_CUTOFFS, **(cutoffs or {})}
    routes = candidate_routes(row, c)
    return all((_state(row.get('metro')) is True,
                _lt(row.get('commune_pop2020_municipal'), c['commune_population']) is True,
                _state(row.get('epci_fp_member')) is True,
                _state(row.get('isolated_L5210_1_1V')) is False,
                _le(row.get('epci_med20'), c['epci_income']) is True,
                _state(row.get('geography_validated')) is True,
                not _missing(row.get('epci_density')),
                routes['B_numerically_possible'] is False,
                routes['C_department'] is False,
                routes['E_overseas'] is False))


def income_domain_candidate(row, cutoffs=None):
    """Income-threshold candidate; mountain must be ruled out. If its population
    share is unknown, return False conservatively unless absence of mountain
    members has been independently verified with a complete frozen list.
    A complete, vintage-correct law-Montagne presence list can also justify
    exclusion of every EPCI with any listed member, without inventing a share.
    """
    c = {**RECONSTRUCTED_CUTOFFS, **(cutoffs or {})}
    routes = candidate_routes(row, c)
    mountain_share = row.get('epci_mountain_population_share')
    mountain_ruled_out = ((not _missing(mountain_share) and mountain_share < .5)
                         or _state(row.get('no_mountain_members_verified')) is True)
    return all((_state(row.get('metro')) is True,
                _lt(row.get('commune_pop2020_municipal'), c['commune_population']) is True,
                _state(row.get('epci_fp_member')) is True,
                _state(row.get('isolated_L5210_1_1V')) is False,
                _le(row.get('epci_density'), c['epci_density']) is True,
                _state(row.get('geography_validated')) is True,
                not _missing(row.get('epci_med20')),
                routes['B_numerically_possible'] is False,
                routes['C_department'] is False,
                mountain_ruled_out,
                routes['E_overseas'] is False))
