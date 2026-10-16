IMG-012: selected native PET-CT DICOM series, 8 April 2026

Research copy prepared from a participant-provided clinical export. Direct record
identifiers, private DICOM elements, overlay planes and JPEG application/comment
metadata were removed. UIDs were consistently replaced. Original pixel values,
image coding, geometry and retained scientific metadata were checked for exact
preservation. No native image pixels were masked or re-encoded.

This is a publicly named research dataset, not an anonymous dataset. Clinical scan
and injection dates/times are retained, as are native anatomical features. Original
record identifiers and private crosswalks are not included.

Corrected PET (BQML) and uncorrected PET (PROPCPS) are distinct series. Rescale,
radiopharmaceutical dose/half-life, timing and body-weight fields were preserved.
No new SUV calibration or diagnostic interpretation is supplied. Check scanner
quantitation assumptions before deriving SUV values; PROPCPS is not BQML.

Every included instance was decoded, screened with two-view OCR and checked for
separate overlays and unused pixel bits. All OCR-flagged regions and first/middle/
last images from each series received visual review. This does not claim an
independent radiologist reread or manual full-resolution review of every slice.

The initial release omits secondary captures/fusions, presentation states, dose
reports, localizer and MIP projections. Optional references to unavailable source
objects were removed; related-series references are retained only within this
release. Original DICOMDIR is omitted; open the DICOM files directly in a compatible
research viewer. JPEG Lossless Process 14 Selection Value 1 decoding is required.

MANIFEST.json lists file SHA-256 values and remapped identifiers. Series completeness
means preservation of all selected instances available in the source export, not
a claim that every original acquisition or every clinical scan is available.
Consult the parent project's data-use terms for reuse and attribution.

Technical references:
https://dicom.nema.org/medical/dicom/current/output/chtml/part15/chapter_E.html
https://pydicom.github.io/pydicom/stable/
