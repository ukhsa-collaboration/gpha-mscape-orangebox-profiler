# Profiler

This code assigns profiles to samples in mSCAPE based on the resulting classified taxa.

## Installation

Clone repo and create environment:
`git clone git@github.com:ukhsa-collaboration/gpha-mscape-clinical-profiles.git`

Installation for users:
`cd gpha-mscape-clinical-profiles`
`pip install .`

Installation for developers (installs code in editable mode):
`cd gpha-mscape-clinical-profiles`
`pip install --editable '.[dev]'`
`pre-commit install`  - this must be run before commiting any changes.


## Usage

This is a library only, and is intended to be used within other codebases.
For example,

```
# Set up a TaxaPlease instance:
from taxaplease import TaxaPlease
tp = TaxaPlease()

# Set up profile lookup dict:
profiles_dict = profiler.make_profiles_dict("path/to/profile/spreadsheet.xlsx")

# Add profiles to a dataframe that contains at least the column 'taxon_id'
my_df_with_profiles = profiler.add_profile_to_results(my_df, profiles_dict, tp)

```
