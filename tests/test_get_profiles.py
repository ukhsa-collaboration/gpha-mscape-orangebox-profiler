"""
Create unit tests for modules in the tests/ folder. All functions in a repo should be unit tested and
tests should be run before and after any changes are made.
"""

import logging

import pandas as pd
import pytest
from taxaplease import TaxaPlease

from profiler import get_profiles as profiler

pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

PATH_TO_TEST_TABLE = "tests/test_profile_tables/test_profile_tables.xlsx"

TEST_PROFILE_NAMES = ["ProfileX", "ProfileC", "ProfileB"]

tp = TaxaPlease()

# haemophilus influenzae is in profileC but genus in profileB

PROFILES_DICT = {
    "ProfileX": {
        1912216: {"taxon": "Cutibacterium spp", "rank": "genus"},
        1386: {"taxon": "Bacillus spp", "rank": "genus"},
        34384: {"taxon": "Arthrodermataceae", "rank": "family"},
        12066: {"taxon": "Coxsackievirus", "rank": "species"},
        3428501: {"taxon": "Rhinovirus A", "rank": "species"},
    },
    "ProfileC": {
        2955465: {"taxon": "Influenza B virus", "rank": "species"},
        77643: {"taxon": "Mycobacterium tuberculosis complex", "rank": "species group"},
        1773: {"taxon": "Mycobacterium tuberculosis", "rank": "species"},
        727: {"taxon": "Haemophilus influenzae", "rank": "species"},
    },
    "ProfileB": {
        3050292: {"taxon": "Herpes simplex virus 1 (HSV-1)", "rank": "species"},
        3050293: {"taxon": "Herpes simplex virus 2 (HSV-2)", "rank": "species"},
        724: {"taxon": "Haemophilus", "rank": "genus"},
    },
}


def test_parse_profile_table():
    table = pd.read_excel(PATH_TO_TEST_TABLE)  # this just gets one tab
    actual_dict = profiler._parse_profile_table_to_dict(table)
    print(actual_dict)
    assert actual_dict == PROFILES_DICT["ProfileX"]


def test_parse_profile_table_bad_columns(caplog):
    # drop a column in the table and save it to tmp path:
    table = pd.read_excel(PATH_TO_TEST_TABLE)  # this just gets one tab
    table = table.rename(columns={"Taxon_ID": "taxonid"})
    expected_err_msg = "Looking for column taxon_id required to parse the profile table"  # column names are lowered.
    with caplog.at_level(logging.ERROR) and pytest.raises(profiler.InputError) as i:
        profiler._parse_profile_table_to_dict(table)

    assert expected_err_msg in caplog.text
    assert expected_err_msg in i.value.message
    print(f"\nIf taxon_id column not in the table, error message is:\n{i.value.message}")


def test_make_profile_dicts():
    profiles_dict = profiler.make_profiles_dict(PATH_TO_TEST_TABLE)
    assert (a := len(profiles_dict)) == (e := len(TEST_PROFILE_NAMES)), (
        f"Expected dictionary with {e} keys, got {a} many keys"
    )
    print(f"Parsed profile dict successfully - {profiles_dict}")


def test_make_profile_dict_no_file(caplog):
    expected_err_msg = "Expected the Profile Tables file at doesnt_exist.file but file not found. Exiting."
    with caplog.at_level(logging.ERROR) and pytest.raises(profiler.InputError) as i:
        profiler.make_profiles_dict("doesnt_exist.file")
    assert expected_err_msg in caplog.text, f"Expected file not found error, got {caplog.text}"
    assert expected_err_msg in i.value.message
    print(f"\nIf file not found, error message is:\n{i.value.message}")


@pytest.mark.parametrize(
    "taxonid,profile",
    [
        (1912216, "ProfileX"),  # cutibacterium
        (1386, "ProfileX"),  # bacillus spp
        (3050293, "ProfileB"),  # Herpes simplex virus 2
        (77643, "ProfileC"),  # Mycobacterium tuberculosis complex
    ],
)
def test__check_profile(taxonid, profile):
    check = profiler._check_profile(taxonid, PROFILES_DICT)
    assert check == profile, f"Expected {profile}, got {check}"
    print(f"\nGot expected profile {check} for taxid: {taxonid}")


@pytest.mark.parametrize(
    "testname,taxonid,profile,rank,profiletaxid,matchname,name",
    [
        ("species in ProfileX", 12066, "ProfileX", "species", 12066, "Coxsackievirus", "Coxsackievirus"),
        ("genus in ProfileX", 1912216, "ProfileX", "genus", 1912216, "Cutibacterium spp", "Cutibacterium spp"),
        ("family in ProfileX", 34384, "ProfileX", "family", 34384, "Arthrodermataceae", "Arthrodermataceae"),
        ("species in genus in ProfileX", 1396, "ProfileX", "genus", 1386, "Bacillus spp", "Bacillus cereus"),
        (
            "species in family in ProfileX",
            2885923,
            "ProfileX",
            "family",
            34384,
            "Arthrodermataceae",
            "Arthroderma lilyanum",
        ),
        (
            "species in ProfileC, genus in ProfileB",
            727,
            "ProfileC",
            "species",
            727,
            "Haemophilus influenzae",
            "Haemophilus influenzae",
        ),
        (
            "genus in ProfileB, species in ProfileC",
            729,
            "ProfileB",
            "genus",
            724,
            "Haemophilus",
            "Haemophilus parainfluenzae",
        ),
        ("taxid is genus where species in tables", 10294, "Unknown", None, None, None, "Simplexvirus"),
        ("taxid not in any profile", 9606, "Unknown", None, None, None, "Homo sapiens"),
    ],
)
def test_check_profile_all_the_way_up(testname, taxonid, profile, rank, profiletaxid, matchname, name):
    (
        actual_profile,
        actual_taxa_name,
        actual_profile_taxon_id,
        actual_taxa_rank,
    ) = profiler.check_profile_all_the_way_up(taxonid, PROFILES_DICT, tp)
    assert actual_profile == profile, f"Expected {profile}, got {actual_profile}"
    assert actual_taxa_name == matchname, f"Expected {matchname}, got {actual_taxa_name}"
    assert actual_taxa_rank == rank, f"Expected {rank}, got {actual_taxa_rank}"
    assert actual_profile_taxon_id == profiletaxid, f"Expected {profiletaxid}, got {actual_profile_taxon_id}"

    print(f"""
    For taxa '{name}' (ID:{taxonid}), expected '{profile}','{matchname}' with taxon id for this {profiletaxid},
    got '{actual_profile}', '{actual_taxa_name}' and '{actual_profile_taxon_id}'
    """)


def test_add_profile_empty_df():
    df = pd.DataFrame()
    actual_df = profiler.add_profile_to_results(df, PROFILES_DICT, tp)
    assert actual_df.empty, (
        f"Expected empty dataframe from add_profile_to_results function when provided empty dataframe, "
        f"instead got {actual_df}"
    )


def test_add_profile_to_results():
    expected_results = pd.DataFrame(
        [
            [2955465, "Influenza B virus", "species", "888", "ProfileC", "Influenza B virus", "2955465", "species"],
            [3016342, "Cutibacterium equinum", "species", "40753", "ProfileX", "Cutibacterium spp", "1912216", "genus"],
            [1434310, "Bacillus sp. #CK-8", "species", "8", "ProfileX", "Bacillus spp", "1386", "genus"],
            [2885923, "Arthroderma lilyanum", "species", "456", "ProfileX", "Arthrodermataceae", "34384", "family"],
            [
                1048245,
                "Mycobacterium canettii CIPT 140010059",
                "no rank",
                "6047",
                "ProfileC",
                "Mycobacterium tuberculosis complex",
                "77643",
                "species group",
            ],
            [
                888828,
                "Haemophilus parainfluenzae ATCC 33392",
                "no rank",
                "123",
                "ProfileB",
                "Haemophilus",
                "724",
                "genus",
            ],
            [2696359, "Butyrivibrio virus Ceridwen", "species", "99999", "Unknown", None, None, None],
        ],
        columns=[
            "taxon_id",
            "human_readable",
            "rank",
            "counts",
            "profile",
            "profile_taxon_match",
            "profile_taxon_id",
            "profile_rank",
        ],
    )
    expected_results["profile_taxon_id"] = expected_results["profile_taxon_id"].astype("Int64")
    taxa_df = expected_results[["taxon_id", "human_readable", "rank", "counts"]]
    actual_results = profiler.add_profile_to_results(taxa_df, PROFILES_DICT, tp)

    assert actual_results.equals(expected_results), (
        "The input taxa to test adding profiels to the dataframe did not match the expected outputs. "
        "This could be due to type mismatches..."
    )
