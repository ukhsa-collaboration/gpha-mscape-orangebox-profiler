"""
get_profiles module includes functionality to parse Profile Tables (as an excel spreadsheet), and
apply the profiles to taxa, either using a single taxon ID or to a dataframe that contains the column 'taxon_id'
"""

import logging
from collections import deque
from pathlib import Path

import pandas as pd
from taxaplease import TaxaPlease


##############
# Exceptions #
class ProfilerError(Exception):
    """Base class for exceptions in this module"""

    pass


class InputError(ProfilerError):
    """
    Exception raised for errors in input files.

    :ivar exitcode: int, exitcode
    :ivar error_type: str, error type caught.
    :ivar message: helpful explicit error message.
    """

    def __init__(self, exitcode: int, error_type: str, message: str):
        """
        Custom Error code - supply exitcode (int) and message (str).
        """
        self.exitcode: int = exitcode
        self.message: str = message
        self.error_type: str = error_type
        self.print_msg: str = f"{self.error_type}: {self.message}"

    def __str__(self):
        return repr(self.print_msg)


#############
# Functions #


def _parse_profile_table_to_dict(profile_df: pd.DataFrame) -> dict:
    """
    Make the profile spreadsheet in dataframe format into a dict with just the taxon_id as the keys, and human readable
    name and rank as key, value pairs as the value.

    :param profile_df: dataframe of the taxa for one profile (e.g. parsed from one tab in the spreadsheet).
    :return: dictionary of taxa belonging to that profile, where key is taxonID and value is a dict of key-value pairs
    of some of the key columns (human readable name, rank).
    :rtype: dict
    """
    # Make all column names lower
    profile_df.columns = [col.lower() for col in profile_df.columns]
    try:
        profile_df["taxon_id"] = profile_df["taxon_id"].astype(int)
        taxon_id_dict = profile_df[["taxon_id", "taxon", "rank"]].set_index("taxon_id").to_dict(orient="index")

    except KeyError as k:
        message = "Looking for column %s required to parse the profile table, not in %s. Exiting." % (
            k.args[0],
            list(profile_df.columns.values),
        )
        logging.error(message)
        raise InputError(1, "KeyError", message) from k

    return taxon_id_dict


def make_profiles_dict(path_to_table: str | Path) -> dict[str, dict[int, str]]:
    """
    Make single dictionary of the profiles:
    'profile' : {taxon_id: human readable ncbi taxonomy name.}

    :param path_to_table: path to the profile table excel spreadsheet (.xlsx)
    :type path_to_table: str | os.PathLike
    :return: profiles_dict. Dictionary of dictionaries, where the outer dict is the profile, and inner dict is taxonid:
    NCBI human readable name.
    :rtype: dict[str, dict[int, str]]
    """
    profiles_dict = {}
    path_to_table = Path(path_to_table)
    try:
        spreadsheet_tabs: dict[str, pd.DataFrame] = pd.read_excel(path_to_table, sheet_name=None)
        profiles = list(spreadsheet_tabs.keys())
        message = "Successfully read spreadsheet %s, with tabs %s." % (path_to_table.stem, ", ".join(profiles))
        logging.info(message)

    except FileNotFoundError as f:
        message = "Expected the Profile Tables file at %s but file not found. Exiting." % (path_to_table)
        logging.error(message)
        raise InputError(1, "FileNotFoundError", message) from f

    # make the dataframes into dicts
    for profile, profile_df in spreadsheet_tabs.items():
        taxon_id_dict = _parse_profile_table_to_dict(profile_df)
        profiles_dict[profile] = taxon_id_dict

    return profiles_dict


def _check_profile(taxon_id: int, profiles_dict: dict) -> str | None:
    """
    Check whether give taxon ID is in the any of the profile dicts.

    :param taxon_id: taxon ID
    :type taxon_id: int
    :param profile_dicts: dictionary of the profile dictionaries, which contain the taxonid: human readable name.
    :type profile_dicts: str
    :return: the profile, or None if not found
    :rtype: str | None
    """
    for profile, profile_dict in profiles_dict.items():
        if taxon_id in profile_dict:
            return profile
    return None


def check_profile_all_the_way_up(
    taxon_id: int, profiles_dict: dict, tp: TaxaPlease
) -> tuple[str, str | None, int | None, str | None]:
    """
    Apply the _check_profile iteratively up the taxanomic ranks from the given taxon_id.

    :param taxon_id: taxon ID
    :type taxon_id: int
    :param profile_dicts: dictionary of the profile dictionaries, which contain the taxonid: human readable name.
    :type profile_dicts: str
    :param taxaplease_instance: instance of taxaplease.
    :type taxaplease_instance: TaxaPlease
    """
    # Set up a queue of IDs to check that are ordered left to right going up the taxonomy ranks.
    taxon_ids_to_check_q = deque()
    family_branch_taxids: tuple = tp.get_all_parent_taxids(taxon_id, includeSelf=True)
    taxon_ids_to_check_q.extend(family_branch_taxids)

    # Check whether the id is a profile
    while taxon_ids_to_check_q:
        id_to_check = taxon_ids_to_check_q.popleft()

        if profile := _check_profile(id_to_check, profiles_dict):
            taxon_name = profiles_dict[profile][id_to_check]["taxon"]
            profile_taxon_id = int(id_to_check)
            rank = profiles_dict[profile][id_to_check]["rank"]

            return profile, taxon_name, profile_taxon_id, rank
    return "Unknown", None, None, None


def add_profile_to_results(taxa_df: pd.DataFrame, profiles_dict: dict, taxaplease_instance: TaxaPlease) -> pd.DataFrame:
    """
    Add the profile, profile taxon match and profile rank to a dataframe using the taxon id.
    Dataframe MUST CONTAIN COLUMN 'taxon_id'.

    :param taxa_df: dataframe that must, at minimum, contain 'taxon_id' column.
    :type taxa_df: pd.DataFrame.
    :return: new taxa_df dataframe with three new columns - "profile", "profile_taxon_match", "profile_rank" (the rank of
    the matched taxa in the profile.)
    :rtype: pd.DataFrame
    """
    if taxa_df.empty:
        return taxa_df

    taxa_df_copy = taxa_df.copy()
    try:
        taxa_df_copy["taxon_id"] = taxa_df_copy["taxon_id"].astype(int)  # Make sure the taxon ID is indeed int.
        taxa_df_copy[["profile", "profile_taxon_match", "profile_taxon_id", "profile_rank"]] = taxa_df_copy.apply(
            lambda row: check_profile_all_the_way_up(row["taxon_id"], profiles_dict, taxaplease_instance),
            axis=1,
            result_type="expand",
        )
        taxa_df_copy["profile_taxon_id"] = taxa_df_copy["profile_taxon_id"].astype("Int64")
    except ValueError as v:
        msg = "Could not add profiles to dataframe; %s" % (v)
        logging.error(msg)
    return taxa_df_copy
