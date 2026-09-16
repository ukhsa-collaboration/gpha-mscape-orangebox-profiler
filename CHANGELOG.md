# Changelog
v2.0.0 - Profiler; use json format instead of xlsx

## Added
- function to parse from json
- unit tests for this
- readme to explain how to parse from json

## Changed
- name of function for parsing from excel is more specific - `make_profiles_dict_from_excel`

---
---
v1.0.1 - Profiler
- pinned taxaplease version

v1.0.0 - Profiler - library
Library with functionality to parse profile tables (xlsx) and check up taxa ids or a dataframe.
- basic functions to parse profile tables (all tabs)
- basic functions to get profile per taxon ID or dataframe with column of taxon ID.
- removed CLI, library only

v.0.1.0 - Profiler (in development)
Assign profiles to taxa - specific add on to ClasPar.
- CLI to run on claspar files
- hierarchical profile assignment
- write an analysis table
