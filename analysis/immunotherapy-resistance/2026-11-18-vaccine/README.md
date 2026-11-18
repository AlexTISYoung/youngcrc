# Immunotherapy resistance and vaccine combination strategy, 18 November 2026

This dated package contains the source for the consolidated immunotherapy-resistance report, including the proposed vactosertib, personalized peptide vaccine, N-803 and checkpoint strategy. It adds reviewed human combination evidence and development/access information. The proposed combination is untested; its components' mechanisms, separate trial results and access enquiries do not establish the safety or efficacy of the complete regimen.

The separately hosted PDF and its final SHA-256, size and page count are recorded in `publication.json`. `report/materialized_content.json` is the exact reviewed report text. The original review article, private correspondence, contact identifiers, raw patient sequencing files and subject-labelled trial matrices are not redistributed.

## Verify and reproduce

From this directory:

```sh
python3 verify_package.py --require-final
python3 verify_package.py --rerun
```

The first command verifies every bundled file, the reviewed publication metadata, source structure and the public-content boundary. The second rebuilds the materialized report source in a temporary directory and compares it with the reviewed source. It does not rerun upstream RNA quantification, proteomics, clinical variant calling or the Monash experiment.

In the complete repository, also verify the inherited source links:

```sh
python3 analysis/immunotherapy-resistance/2026-11-18-vaccine/verify_package.py --require-repository-dependencies
```

`provenance/inherited_dependencies.json` pins preserved public packages and exact files that underpin the inherited numerical evidence. They are retained in their original dated repository locations. A standalone download of this package can verify its bundled inputs without downloading those historical packages; the repository-dependent check requires the complete Git checkout.

To recreate the editable document, install `report/requirements.txt` and run `report/build_revision.py`. PDF conversion additionally requires a compatible document-rendering environment. Font, layout-engine and timestamp differences can change rendered PDF bytes; the reviewed published artifact is identified by its exact hash, not by a claim that every rendering is byte-identical. Document generation is separate from deterministic source assembly.

## Evidence boundaries

- Archival biopsy, treated resection, liver observations and current-lesion uncertainty remain distinct. Expression, protein abundance and pathway activation are not interchangeable.
- The complete 28-sample vactosertib trial RNA analysis remains unchanged: durable clinical benefit five versus 23; four prespecified pathway comparisons all BH-adjusted q=0.521. These findings do not validate pathway expression as a predictor of benefit or rule out benefit.
- Randomized adjuvant melanoma vaccine benefit does not provide a response probability in active metastatic colorectal cancer. Advanced-disease and colorectal combination counterevidence is retained.
- Five added mechanistic leads retain discussion priority 5. These rankings are research priorities, not response probabilities. Access information is dated, agent-specific and subject to confirmation; a clinician enquiry or access list is not confirmed supply or approved administration.
- The previously reviewed exact-variant SMAD4 communication remains attributed evidence supporting functional impairment and PS3 while the overall assessment remains a variant of uncertain significance. The original email, unpublished figure and raw experimental values are excluded.

The repository's root clinical/site snapshot remains historical website release 1.53. This dated report addition does not refresh those tables or establish that a proposed treatment was administered. Previous dated packages remain available as historical provenance.
