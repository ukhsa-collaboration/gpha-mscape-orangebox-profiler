# Profiler

This code assigns profiles to samples in mSCAPE based on the resulting classified taxa.

## Installation

Clone repo and create environment:
`git clone git@github.com:ukhsa-collaboration/gpha-mscape-orangebox-profiler.git`

Installation for users:

`cd gpha-mscape-orangebox-profiler`

`pip install .`

Installation for developers (installs code in editable mode):

`cd cd gpha-mscape-orangebox-profiler`

`pip install --editable '.[dev]'`

`pre-commit install`  - this must be run before commiting any changes.


## Usage

This is a library only, and is intended to be used within other codebases. First, read in
the profile look up file:


    ## json:
    Use function `get_profiles_and_metadata_from_json` and provide path to json. this must have
    'metadata' and 'profiles' at the top level, else an InputError will be raised.

    ## xlsx:
    Use function `make_profiles_dict_from_excel` and provide path to xlsx.


Once the lookup is read in, it is possible to look up either a single taxon ID using `check_profile_all_the_way_up` or
add the profile, rank and name to a dataframe that contains at least a taxon ID column using `add_profile_to_results`.

For example:

```
from profiler import get_profiles as profiler
from taxaplease import TaxaPlease

# Set up a TaxaPlease instance:
tp = TaxaPlease()

# Set up profile lookup dict:
# Either from json (which should provide metadata)
profiles_dict, metadata = get_profiles_and_metadata_from_json(Path("path/to/file.json"))

# or from xlsx:
profiles_dict = profiler.make_profiles_dict_from_excel("path/to/profile/spreadsheet.xlsx")

# To look up just one taxid:
profile, name, taxon_id, rank = profiler.check_profile_all_the_way_up(taxon_id, profiles_dict, tp)

# Add profiles to a dataframe that contains at least the column 'taxon_id'
my_df_with_profiles = profiler.add_profile_to_results(my_df, profiles_dict, tp)

```
