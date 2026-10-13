"""Demo data: sample SOP PDFs (generated with PyMuPDF), reagents, verified fixes,
profiles, projects, experiments, datasets and equipment.

Seeding only runs against an empty database, so it never overwrites real data.
The SOP PDFs go through the same validation + ingestion pipeline as uploads.
"""
from __future__ import annotations

import io
import json
import logging
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pymupdf as fitz
from werkzeug.datastructures import FileStorage

from .db import get_setting, set_setting, transaction_lock
from .security import DOCUMENT_EXTENSIONS, validate_upload

logger = logging.getLogger(__name__)

DEMO_SOPS: list[dict] = [
    {
        "filename": "SOP-HPLC-004_HPLC_Operation_and_Troubleshooting.pdf",
        "title": "SOP-HPLC-004 HPLC Operation and Troubleshooting",
        "meta": {"category": "Instrument", "doc_code": "SOP-HPLC-004", "version": "3.1", "owner": "Jordan Lee", "approval_status": "approved"},
        "pages": [
            "SOP-HPLC-004 HPLC Operation and Troubleshooting\n\n1. Purpose and Scope\nThis procedure describes the "
            "start-up, routine operation and first-line troubleshooting of the analytical HPLC systems in Lab 2.14. "
            "It applies to all analysts trained on reversed-phase methods.\n\n2. Safety\nWear safety glasses, a lab "
            "coat and nitrile gloves. Mobile phases containing acetonitrile or methanol are flammable and must be "
            "handled in a ventilated area. Never open a pressurised fitting while the pump is running.",
            "3. System Start-up\nDegas all mobile phases by sonication for 10 minutes or use the inline degasser. "
            "Filter aqueous buffers through a 0.22 um membrane before use. Purge each pump channel at 5 mL/min for "
            "3 minutes with the purge valve open. Close the purge valve and ramp the flow to the method flow rate over "
            "2 minutes. Equilibrate the column with at least 10 column volumes of the starting mobile phase until the "
            "baseline drift is below 1 mAU per 10 minutes.",
            "4. Troubleshooting High Back-Pressure (Error E-104)\nError E-104 indicates that system pressure exceeded "
            "the upper pressure limit of 400 bar and the pump stopped. First, disconnect the column and run the pump "
            "at 1 mL/min. If pressure remains above 20 bar without the column, the blockage is in the system: replace "
            "the inline filter frit and check the injector rotor seal. If pressure is normal without the column, back-"
            "flush the guard column or replace it. Buffer precipitation is a common cause when gradients exceed 80% "
            "organic solvent; flush the system with warm water at 40 C before switching to organic solvent.\n\n"
            "5. Baseline Noise and Drift\nExcessive baseline noise usually indicates air bubbles in the detector flow "
            "cell or a failing lamp. Purge the pump, flush the flow cell with isopropanol, and check the lamp hours. "
            "Replace the deuterium lamp after 2000 hours of use.",
            "6. Shutdown and Column Storage\nAt the end of the day flush buffer-containing columns with 10 column volumes "
            "of 10% methanol in water, then store reversed-phase columns in 80% acetonitrile. Cap both column ends. Record "
            "column usage, pressure and any faults in the instrument logbook. Report repeated E-104 errors to the "
            "instrument owner.",
        ],
    },
    {
        "filename": "SOP-CC-011_Mammalian_Cell_Culture.pdf",
        "title": "SOP-CC-011 Mammalian Cell Culture: Passaging HEK293 Cells",
        "meta": {"category": "Cell culture", "doc_code": "SOP-CC-011", "version": "2.0", "owner": "Priya Raman", "approval_status": "approved"},
        "pages": [
            "SOP-CC-011 Mammalian Cell Culture: Passaging HEK293 Cells\n\n1. Scope\nThis SOP covers thawing, passaging "
            "and routine monitoring of adherent HEK293 cells in a Class II biological safety cabinet. All work is "
            "performed under BSL-2 conditions.\n\n2. Thawing Cells\nThaw the cryovial in a 37 C water bath for 1 to 2 "
            "minutes until a small ice crystal remains. Transfer the cells dropwise into 9 mL of pre-warmed complete "
            "DMEM with 10% FBS. Centrifuge at 200 x g for 5 minutes and resuspend in fresh medium.",
            "3. Passaging Procedure\nPassage cells at 80 to 90% confluence. Aspirate the medium and rinse once with "
            "PBS without calcium and magnesium. Add 1 mL of 0.05% trypsin-EDTA per T75 flask and incubate at 37 C for "
            "3 to 5 minutes until cells detach. Neutralise with 9 mL complete medium, count with trypan blue, and seed "
            "new flasks at 2 x 10^4 cells per cm2. Do not exceed passage number 25.\n\n4. Reagent Storage\nStore "
            "trypsin-EDTA aliquots at -20 C and avoid repeated freeze-thaw cycles. Thawed trypsin may be kept at 4 C "
            "for up to two weeks. Store complete DMEM at 4 C for up to 4 weeks.",
            "5. Suspected Contamination Response\nIf medium becomes cloudy, changes colour rapidly to yellow, or "
            "unusual particles or filaments are observed, do not attempt to identify the contaminant by eye. Close the "
            "flask, label it QUARANTINE, and move it to the quarantine incubator. Disinfect the biosafety cabinet with "
            "70% ethanol followed by a 10% bleach wipe. Submit a sample for mycoplasma PCR and sterility testing and "
            "notify the cell culture lead. Discard affected cultures by autoclaving if testing confirms contamination.",
        ],
    },
    {
        "filename": "SOP-CEN-002_Benchtop_Centrifuge.pdf",
        "title": "SOP-CEN-002 Benchtop Centrifuge Operation",
        "meta": {"category": "Instrument", "doc_code": "SOP-CEN-002", "version": "2.0-draft", "owner": "Jordan Lee", "approval_status": "pending"},
        "pages": [
            "SOP-CEN-002 Benchtop Centrifuge Operation\n\n1. Balancing the Rotor\nAlways load tubes in opposing "
            "positions with matched volumes within 0.1 g. Use balance tubes filled with water when the sample count is "
            "odd. Inspect buckets and adapters for cracks before each run.\n\n2. Imbalance Error (IMB-01)\nThe IMB-01 "
            "error is displayed when the imbalance sensor detects excessive vibration; the run decelerates and stops. "
            "Wait until the rotor has completely stopped and the lid unlocks. Reweigh the tubes, redistribute them "
            "symmetrically, and restart the run. If IMB-01 repeats with a balanced load, tag the centrifuge out of "
            "service and contact the equipment owner.",
            "3. Lid Lock Error (LID-12)\nLID-12 indicates that the lid is not latched. Press the lid firmly at the "
            "centre until it clicks. Never attempt to override the lid interlock. If the error persists, the latch "
            "sensor may require service.\n\n4. Aerosol Containment\nUse sealed buckets for biological samples. Open "
            "sealed buckets inside the biosafety cabinet. If a tube breaks, leave the lid closed for 30 minutes to "
            "allow aerosols to settle before cleaning with an approved disinfectant.",
        ],
    },
    {
        "filename": "SOP-SAF-001_Chemical_Spill_and_Exposure.pdf",
        "title": "SOP-SAF-001 Chemical Spill and Exposure Response",
        "meta": {"category": "Safety", "doc_code": "SOP-SAF-001", "version": "4.0", "owner": "Sam Novak", "approval_status": "approved"},
        "pages": [
            "SOP-SAF-001 Chemical Spill and Exposure Response\n\n1. Minor Spills (under 500 mL)\nAlert people nearby, "
            "put on appropriate PPE and contain the spill with absorbent pads from the spill kit, working from the "
            "outside in. Collect waste in a labelled hazardous waste bag. Consult the Safety Data Sheet for the "
            "specific neutralisation agent.\n\n2. Major Spills\nEvacuate the area, close the doors and call the EHS "
            "emergency line. Do not attempt to clean up a major spill alone.",
            "3. Skin and Eye Exposure\nFor eye exposure, flush immediately at the eyewash station for at least 15 "
            "minutes, holding the eyelids open. For skin exposure, remove contaminated clothing and rinse under the "
            "safety shower for 15 minutes. Seek medical attention and bring the Safety Data Sheet. Report every "
            "exposure to the lab manager and EHS within 24 hours.\n\n4. Unknown or Unlabelled Materials\nTreat any "
            "unlabelled container as hazardous. Do not open, smell or attempt to identify the contents. Isolate it in "
            "secondary containment and request characterisation through EHS.",
        ],
    },
]


DEMO_SOPS.append({
    "filename": "SOP-CC-011_v1_Mammalian_Cell_Culture.pdf",
    "title": "SOP-CC-011 Mammalian Cell Culture: Passaging HEK293 Cells",
    "meta": {"category": "Cell culture", "doc_code": "SOP-CC-011", "version": "1.0", "owner": "Priya Raman",
             "approval_status": "outdated"},
    "pages": [
        "SOP-CC-011 Mammalian Cell Culture: Passaging HEK293 Cells (version 1.0)\n\n1. Scope\nThis superseded SOP "
        "covered passaging of adherent HEK293 cells.\n\n2. Passaging Procedure\nAdd 2 mL of 0.25% trypsin-EDTA per "
        "T75 flask and incubate at 37 C for 8 to 10 minutes until cells detach. Do not exceed passage number 30.",
    ],
})


# Compound reference data for the lab co-pilot (DEMO DATA). Molecular weights in g/mol.
# Mixtures (media, buffers sold as a mix, enzyme solutions) have no single molecular weight, so
# it is left empty and the calculator refuses rather than guessing.
# Note: "Tris" alone is deliberately not a synonym of either Tris form, so it resolves as ambiguous.
DEMO_COMPOUNDS: list[tuple[str, str, float | None, str | None, str]] = [
    # key, display name, MW, CAS, synonyms (;-separated)
    ("tris_base", "Tris base", 121.14, "77-86-1",
     "Trizma base; tris(hydroxymethyl)aminomethane; tromethamine; THAM"),
    ("tris_hcl", "Tris-HCl", 157.60, "1185-53-1", "Tris hydrochloride; Trizma hydrochloride"),
    ("sodium_chloride", "Sodium chloride", 58.44, "7647-14-5", "NaCl"),
    ("potassium_chloride", "Potassium chloride", 74.55, "7447-40-7", "KCl"),
    ("magnesium_chloride_hexahydrate", "Magnesium chloride hexahydrate", 203.30, "7791-18-6",
     "MgCl2 hexahydrate; MgCl2.6H2O"),
    ("edta_disodium_dihydrate", "EDTA disodium salt dihydrate", 372.24, "6381-92-6",
     "Na2EDTA dihydrate; disodium EDTA; EDTA disodium"),
    ("glycine", "Glycine", 75.07, "56-40-6", "aminoacetic acid"),
    ("sds", "Sodium dodecyl sulfate", 288.38, "151-21-3", "SDS; sodium lauryl sulfate"),
    ("sodium_hydroxide", "Sodium hydroxide", 40.00, "1310-73-2", "NaOH; caustic soda"),
    ("hydrochloric_acid", "Hydrochloric acid", 36.46, "7647-01-0", "HCl; muriatic acid"),
    ("sodium_hypochlorite", "Sodium hypochlorite", 74.44, "7681-52-9", "bleach; NaOCl; hypochlorite"),
    ("ammonium_hydroxide", "Ammonium hydroxide", 35.05, "1336-21-6", "ammonia solution; NH4OH"),
    ("hydrogen_peroxide", "Hydrogen peroxide", 34.01, "7722-84-1", "H2O2"),
    ("acetone", "Acetone", 58.08, "67-64-1", "propanone"),
    ("ethanol", "Ethanol", 46.07, "64-17-5", "EtOH; ethyl alcohol; absolute ethanol"),
    ("methanol", "Methanol", 32.04, "67-56-1", "MeOH; methyl alcohol"),
    ("acetonitrile", "Acetonitrile", 41.05, "75-05-8", "ACN; MeCN"),
    ("dmso", "Dimethyl sulfoxide", 78.13, "67-68-5", "DMSO"),
    ("trypan_blue", "Trypan blue", 960.81, "72-57-1", ""),
    ("pbs", "Phosphate-buffered saline", None, None, "PBS"),
    ("trypsin_edta", "Trypsin-EDTA", None, None, "trypsin"),
    ("dmem", "DMEM", None, None, "Dulbecco's modified Eagle medium"),
    ("fbs", "Fetal bovine serum", None, None, "FBS"),
]

# Demo inventory lot name -> compound key (links seeded lots to the reference data).
DEMO_LOT_COMPOUNDS = {
    "Ethanol, absolute (200 proof)": "ethanol", "Acetonitrile, HPLC grade": "acetonitrile",
    "Methanol, HPLC grade": "methanol", "Trypsin-EDTA 0.05%": "trypsin_edta", "DMEM, high glucose": "dmem",
    "Fetal Bovine Serum": "fbs", "Phosphate-buffered saline (no Ca/Mg)": "pbs", "Trypan blue 0.4%": "trypan_blue",
    "Sodium hydroxide pellets": "sodium_hydroxide", "Bleach (sodium hypochlorite 10%)": "sodium_hypochlorite",
    "DMSO, cell culture grade": "dmso",
}


def seed_compounds(conn: sqlite3.Connection) -> None:
    """Load the demo compound reference data once, and link demo inventory lots to it."""
    transaction_lock(conn, "seed")
    if conn.execute("SELECT COUNT(*) FROM compounds").fetchone()[0]:
        conn.rollback()
        return
    conn.executemany(
        "INSERT INTO compounds (compound_key, display_name, molecular_weight, cas_number, synonyms) VALUES (?, ?, ?, ?, ?)",
        DEMO_COMPOUNDS)
    conn.executemany("UPDATE reagents SET compound_key = ? WHERE name = ? AND compound_key IS NULL",
                     [(key, name) for name, key in DEMO_LOT_COMPOUNDS.items()])
    conn.commit()
    logger.info("Seeded %d demo compounds.", len(DEMO_COMPOUNDS))


# ---------------------------------------------------------------------------------------------
# Lab co-pilot demo data (DEMO DATA: original sample SOPs written for this demo, not real procedures).
# ---------------------------------------------------------------------------------------------
_DEMO_BANNER = ("DEMO DATA - written for the SmartLab AI demonstration. This is not an approved laboratory "
                "procedure.")

DEMO_AGENT_SOPS: list[dict] = [
    {
        "filename": "SOP-BUF-001_TNE_Buffer_demo.pdf",
        "title": "SOP-BUF-001 Preparation of Tris-NaCl-EDTA (TNE) Buffer (demo SOP)",
        "meta": {"category": "Reagent preparation", "doc_code": "SOP-BUF-001", "version": "1.0", "owner": "Demo data",
                 "approval_status": "approved"},
        "pages": [
            "SOP-BUF-001 Preparation of Tris-NaCl-EDTA (TNE) Buffer, pH 8.0\n\n" + _DEMO_BANNER + "\n\n"
            "1. Purpose\nThis procedure describes the preparation of TNE buffer containing Tris base, sodium chloride "
            "and EDTA disodium salt dihydrate. The mass of each component is calculated from its molecular weight, "
            "the target concentration and the final volume required.\n\n"
            "2. Safety\nWear safety glasses, a lab coat and nitrile gloves. Hydrochloric acid is corrosive: add it "
            "slowly, in a fume hood, and never add water to concentrated acid. Tris base and EDTA powders are "
            "irritants; avoid creating dust when weighing.",
            "3. Procedure\nWeigh the calculated mass of Tris base, sodium chloride and EDTA disodium salt dihydrate on a "
            "calibrated balance using a clean weighing boat. Transfer the solids to a clean beaker and dissolve them in "
            "deionised water equal to about 80% of the final volume, stirring with a magnetic stirrer. Calibrate the pH "
            "meter before use. Adjust the pH to 8.0 by adding hydrochloric acid dropwise while stirring. Transfer the "
            "solution to a volumetric flask and make up to the final volume with deionised water. Filter through a "
            "0.22 um membrane filter into a sterile, labelled bottle.\n\n"
            "4. Storage and Labelling\nLabel the bottle with the buffer name, pH, date and your initials. Store at 4 C "
            "and use within 1 month. Discard the buffer if it becomes cloudy.",
        ],
    },
    {
        "filename": "SOP-BUF-002_Salt_Stock_Solutions_demo.pdf",
        "title": "SOP-BUF-002 Preparation of Salt Stock Solutions (demo SOP)",
        "meta": {"category": "Reagent preparation", "doc_code": "SOP-BUF-002", "version": "1.0", "owner": "Demo data",
                 "approval_status": "approved"},
        "pages": [
            "SOP-BUF-002 Preparation of Salt Stock Solutions (NaCl, KCl, MgCl2)\n\n" + _DEMO_BANNER + "\n\n"
            "1. Scope\nThis procedure covers sodium chloride, potassium chloride and magnesium chloride hexahydrate "
            "stock solutions prepared by weight.\n\n"
            "2. Safety\nWear safety glasses, a lab coat and gloves. Clean up spilled salt promptly; wet floors are "
            "slippery.\n\n"
            "3. Procedure\nCalculate the mass of salt from its molecular weight, the target concentration and the final "
            "volume. Weigh the salt and dissolve it in deionised water equal to about 80% of the final volume. "
            "Magnesium chloride hexahydrate is hygroscopic: weigh it quickly and keep the container closed. Make up to "
            "the final volume with deionised water and mix by inversion. Sterilise by autoclaving at 121 C for 20 "
            "minutes or filter through a 0.22 um membrane.\n\n"
            "4. Storage\nStore sodium chloride and potassium chloride stocks at room temperature for up to 6 months. "
            "Store magnesium chloride solutions at 4 C.",
        ],
    },
    {
        "filename": "SOP-BUF-003_Tris_Glycine_SDS_Running_Buffer_demo.pdf",
        "title": "SOP-BUF-003 Preparation of Tris-Glycine-SDS Running Buffer (demo SOP)",
        "meta": {"category": "Reagent preparation", "doc_code": "SOP-BUF-003", "version": "1.0", "owner": "Demo data",
                 "approval_status": "approved"},
        "pages": [
            "SOP-BUF-003 Preparation of Tris-Glycine-SDS Running Buffer\n\n" + _DEMO_BANNER + "\n\n"
            "1. Composition\nThe 1x running buffer contains 25 mM Tris base, 192 mM glycine and 0.1% w/v sodium dodecyl "
            "sulfate (SDS).\n\n"
            "2. Safety\nSDS powder is a respiratory irritant: weigh it in a fume hood or wear a dust mask. Wear gloves "
            "and safety glasses.\n\n"
            "3. Procedure\nDissolve the Tris base and glycine in deionised water equal to about 80% of the final volume. "
            "Add the SDS last and stir gently to avoid foaming. Do not adjust the pH; it should be about 8.3. Make up "
            "to the final volume with deionised water.\n\n"
            "4. Storage\nStore at room temperature and use within 1 month.",
        ],
    },
    {
        "filename": "SOP-DEC-004_Bench_Decontamination_demo.pdf",
        "title": "SOP-DEC-004 Bench Decontamination with Bleach (demo SOP)",
        "meta": {"category": "Safety", "doc_code": "SOP-DEC-004", "version": "1.0", "owner": "Demo data",
                 "approval_status": "approved"},
        "pages": [
            "SOP-DEC-004 Bench Decontamination with Bleach\n\n" + _DEMO_BANNER + "\n\n"
            "1. Working Solution\nPrepare a 1% w/v sodium hypochlorite working solution fresh each day by diluting the "
            "stock bleach with water. Apply it to the surface and leave a contact time of 10 minutes, then wipe the "
            "surface with water.\n\n"
            "2. Safety\nNever mix bleach with acids, ammonia or alcohols such as ethanol: toxic gases or chlorinated "
            "by-products can form. Wear gloves and safety glasses and work with good ventilation. Use 70% ethanol only "
            "after the bleach has been fully wiped off with water.",
        ],
    },
    {
        "filename": "SOP-PHM-005_pH_Meter_Error_Codes_demo.pdf",
        "title": "SOP-PHM-005 PHM-200 pH Meter Calibration and Error Codes (demo SOP)",
        "meta": {"category": "Instrument", "doc_code": "SOP-PHM-005", "version": "1.0", "owner": "Demo data",
                 "approval_status": "approved"},
        "pages": [
            "SOP-PHM-005 PHM-200 pH Meter Calibration and Error Codes\n\n" + _DEMO_BANNER + "\n\n"
            "1. Calibration\nCalibrate the meter daily with pH 4.01, 7.00 and 10.01 buffers at room temperature. Rinse "
            "the electrode with deionised water between buffers and blot it dry with lint-free tissue; never wipe the "
            "glass bulb.\n\n"
            "2. Error CAL-02 (slope out of range)\nCAL-02 means the electrode slope is outside 90 to 105%. Replace the "
            "calibration buffers with fresh ones and repeat the calibration. If CAL-02 persists, clean the electrode by "
            "soaking it in 0.1 M HCl for 15 minutes, rinse, and recalibrate. Replace the electrode if the error "
            "continues.",
            "3. Error ERR-07 (unstable reading)\nERR-07 means the reading did not stabilise within 60 seconds. Check "
            "that the electrode junction is wet and that the reference fill solution covers the internal element. "
            "Refill with 3 M KCl if the level is low. Store the electrode in storage solution, never in deionised "
            "water.\n\n"
            "4. Safety\nWear safety glasses and gloves when handling the hydrochloric acid cleaning solution.",
        ],
    },
]

# (name, compound_key, quantity, unit, reorder_threshold, location, expiry offset in days, category)
DEMO_AGENT_LOTS = [
    ("Tris base, molecular biology grade (demo)", "tris_base", 500, "g", 100, "Chemical store B, shelf 2", 300, "Buffer salt"),
    ("Tris-HCl (demo, expired lot)", "tris_hcl", 250, "g", 50, "Chemical store B, shelf 2", -20, "Buffer salt"),
    ("Sodium chloride, ACS grade (demo)", "sodium_chloride", 1, "kg", 0.2, "Chemical store B, shelf 1", 500, "Buffer salt"),
    ("EDTA disodium salt dihydrate (demo)", "edta_disodium_dihydrate", 100, "g", 20, "Chemical store B, shelf 3", 200,
     "Buffer salt"),
    ("Glycine (demo, low stock)", "glycine", 40, "g", 50, "Chemical store B, shelf 3", 400, "Buffer salt"),
    ("SDS, electrophoresis grade (demo, expiring)", "sds", 50, "g", 10, "Chemical store B, shelf 4", 12, "Detergent"),
    ("Potassium chloride (demo, small lot)", "potassium_chloride", 5, "g", 25, "Chemical store B, shelf 1", 300,
     "Buffer salt"),
    ("Hydrochloric acid 37% (demo)", "hydrochloric_acid", 2.5, "L", 0.5, "Corrosives cabinet C2", 700, "Acid"),
]

# (error_code, equipment, symptom, keywords, probable_cause, fix, source_document, source_page, machine_model, ppe)
DEMO_AGENT_FIXES = [
    ("CAL-02", "pH meter", "Calibration fails with slope out of range", "calibration, slope, cal fail, buffer, electrode",
     "Old calibration buffers or a dirty electrode",
     "Replace the calibration buffers with fresh ones and repeat the calibration. If CAL-02 persists, clean the "
     "electrode by soaking it in 0.1 M HCl for 15 minutes, rinse, and recalibrate. Replace the electrode if the error "
     "continues.", "SOP-PHM-005 PHM-200 pH Meter Calibration and Error Codes (demo SOP)", 1,
     "PHM-200 benchtop pH meter (demo instrument)",
     "Wear safety glasses and nitrile gloves when handling the hydrochloric acid cleaning solution."),
    ("ERR-07", "pH meter", "Reading does not stabilise", "unstable, drifting, not stable, junction, reference, fill",
     "Dry junction or low reference fill solution",
     "Check that the electrode junction is wet and that the reference fill solution covers the internal element. "
     "Refill with 3 M KCl if the level is low.", "SOP-PHM-005 PHM-200 pH Meter Calibration and Error Codes (demo SOP)",
     2, "PHM-200 benchtop pH meter (demo instrument)", "Wear safety glasses and gloves when refilling the electrode."),
]

# Machine model and PPE notes for the troubleshooting entries seeded by seed_records().
DEMO_FIX_DETAILS = {
    "E-104": ("Analytical HPLC #2, quaternary pump (demo instrument)",
              "Wear safety glasses, a lab coat and nitrile gloves. Never open a pressurised fitting while the pump is "
              "running."),
    "IMB-01": ("Refrigerated benchtop centrifuge (demo instrument)",
               "Wait for the rotor to stop completely before opening the lid. Use sealed buckets for biological samples."),
    "LID-12": ("Refrigerated benchtop centrifuge (demo instrument)", "Never override the lid interlock."),
}


def seed_agent_demo(conn: sqlite3.Connection, rag_engine, upload_dir: Path, max_bytes: int) -> None:
    """Add the lab co-pilot demo data (SOPs, stock lots, fixes) once, and only to a demo database.

    A database counts as a demo database when seed_records() populated it, so real data is never mixed
    with demo rows.
    """
    from .rag.engine import DuplicateDocumentError

    transaction_lock(conn, "seed")
    if get_setting(conn, "demo_agent_data") == "true" or get_setting(conn, "demo_records") != "true":
        conn.rollback()
        return
    for sop in DEMO_AGENT_SOPS:
        data = build_pdf(sop["title"], sop["pages"])
        upload = FileStorage(stream=io.BytesIO(data), filename=sop["filename"], content_type="application/pdf")
        validated = validate_upload(upload, DOCUMENT_EXTENSIONS, max_bytes=max_bytes)
        try:
            rag_engine.ingest(conn, validated, upload_dir, title=sop["title"], doc_type="SOP", metadata=sop["meta"])
        except DuplicateDocumentError:
            pass
    transaction_lock(conn, "seed")
    conn.executemany(
        "INSERT INTO reagents (name, compound_key, quantity, unit, reorder_threshold, location, expiry_date, category, "
        "supplier, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Demo supplier', 'DEMO DATA')",
        [(n, k, q, u, t, loc, _d(days), cat) for n, k, q, u, t, loc, days, cat in DEMO_AGENT_LOTS])
    conn.executemany(
        "INSERT INTO troubleshooting (error_code, equipment, symptom, keywords, probable_cause, fix, source_document, "
        "source_page, machine_model, ppe_warning) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", DEMO_AGENT_FIXES)
    conn.executemany("UPDATE troubleshooting SET machine_model = ?, ppe_warning = ? WHERE error_code = ? "
                     "AND machine_model IS NULL", [(m, p, code) for code, (m, p) in DEMO_FIX_DETAILS.items()])
    set_setting(conn, "demo_agent_data", "true")
    conn.commit()
    logger.info("Seeded lab co-pilot demo data (%d SOPs, %d lots).", len(DEMO_AGENT_SOPS), len(DEMO_AGENT_LOTS))


def write_demo_sop_pdfs(target: Path) -> list[Path]:
    """Write the co-pilot demo SOPs as text-based PDFs (used to refresh sample_data/sops)."""
    target.mkdir(parents=True, exist_ok=True)
    paths = []
    for sop in DEMO_AGENT_SOPS:
        path = target / sop["filename"]
        path.write_bytes(build_pdf(sop["title"], sop["pages"]))
        paths.append(path)
    return paths


def build_pdf(title: str, pages: list[str]) -> bytes:
    doc = fitz.open()
    doc.set_metadata({"title": title, "author": "SmartLab AI demo", "subject": "Standard Operating Procedure"})
    for number, text in enumerate(pages, start=1):
        page = doc.new_page(width=595, height=842)  # A4
        page.insert_textbox(fitz.Rect(56, 56, 539, 780), text, fontsize=10.5, fontname="helv", lineheight=1.35)
        page.insert_text((56, 815), f"{title}  -  Page {number} of {len(pages)}", fontsize=8, color=(0.4, 0.4, 0.4))
    data = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return data


def _d(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def seed_documents(conn: sqlite3.Connection, rag_engine, upload_dir: Path, max_bytes: int) -> None:
    transaction_lock(conn, "seed")  # another server process may be seeding the same PostgreSQL database
    if conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]:
        conn.rollback()  # end the read transaction (releases the lock on PostgreSQL)
        return
    for sop in DEMO_SOPS:
        data = build_pdf(sop["title"], sop["pages"])
        upload = FileStorage(stream=io.BytesIO(data), filename=sop["filename"], content_type="application/pdf")
        validated = validate_upload(upload, DOCUMENT_EXTENSIONS, max_bytes=max_bytes)
        rag_engine.ingest(conn, validated, upload_dir, title=sop["title"], doc_type="SOP", metadata=sop["meta"])
    set_setting(conn, "demo_documents", "true")
    conn.commit()
    logger.info("Seeded %d demo SOP documents.", len(DEMO_SOPS))


def seed_records(conn: sqlite3.Connection) -> None:
    transaction_lock(conn, "seed")  # held until the single commit below on PostgreSQL
    if conn.execute("SELECT COUNT(*) FROM reagents").fetchone()[0]:
        conn.rollback()
        return
    reagents = [
        ("Ethanol, absolute (200 proof)", "64-17-5", "EtOH-2500", "L23-0412", 3.5, "L", 2, "Flammables cabinet F2", "Room temperature, flammables cabinet", "Flammable liquid (3)", _d(400), "Generic Supplier A"),
        ("Acetonitrile, HPLC grade", "75-05-8", "ACN-4L", "L23-1180", 1.2, "L", 4, "Flammables cabinet F1", "Room temperature, tightly closed, flammables cabinet", "Flammable liquid (3), acute tox (4)", _d(210), "Generic Supplier B"),
        ("Methanol, HPLC grade", "67-56-1", "MEOH-4L", "L24-0077", 8, "L", 4, "Flammables cabinet F1", "Room temperature, flammables cabinet", "Flammable liquid (2), toxic (3)", _d(520), "Generic Supplier B"),
        ("Trypsin-EDTA 0.05%", None, "TRY-100", "T24-3391", 6, "aliquot", 10, "Freezer -20 C, rack B", "-20 C; thawed aliquots 4 C up to 2 weeks", None, _d(18), "Cell Media Co."),
        ("DMEM, high glucose", None, "DMEM-500", "D24-1022", 4, "bottle", 3, "Cold room 4 C, shelf 2", "2-8 C, protect from light", None, _d(45), "Cell Media Co."),
        ("Fetal Bovine Serum", None, "FBS-500", "F23-0099", 2, "bottle", 2, "Freezer -20 C, rack A", "-20 C; avoid freeze-thaw", None, _d(-12), "Cell Media Co."),
        ("Phosphate-buffered saline (no Ca/Mg)", None, "PBS-1L", "P24-5550", 12, "L", 5, "Room 2.14 shelf 4", "Room temperature", None, _d(300), "Generic Supplier A"),
        ("Trypan blue 0.4%", "72-57-1", "TB-100", "TB24-010", 90, "mL", 20, "Room 2.14 shelf 3", "Room temperature", "Carcinogenicity (1B)", _d(150), "Generic Supplier C"),
        ("SYBR Green qPCR master mix", None, "SYBR-5ML", "S24-8810", 1.5, "mL", 2, "Freezer -20 C, rack C", "-20 C, protect from light", None, _d(25), "Molecular Kits Ltd."),
        ("Sodium hydroxide pellets", "1310-73-2", "NAOH-500G", "N22-4410", 450, "g", 100, "Corrosives cabinet C1", "Room temperature, dry, corrosives cabinet", "Skin corrosion (1A)", _d(900), "Generic Supplier A"),
        ("Bleach (sodium hypochlorite 10%)", "7681-52-9", "HYP-1L", "H24-1201", 0.4, "L", 1, "Under-sink cabinet", "Room temperature, away from acids", "Skin corrosion (1B)", _d(60), "Generic Supplier C"),
        ("DMSO, cell culture grade", "67-68-5", "DMSO-100", "DM24-332", 80, "mL", 25, "Room 2.14 shelf 3", "Room temperature, protect from moisture", None, _d(-40), "Generic Supplier B"),
    ]
    categories = ["Solvent", "Solvent", "Solvent", "Cell culture", "Cell culture", "Cell culture", "Buffer", "Stain",
                  "Molecular biology", "Base", "Disinfectant", "Solvent"]
    conn.executemany(
        "INSERT INTO reagents (name, cas_number, catalog_number, lot_number, quantity, unit, reorder_threshold, location, "
        "storage_condition, hazard_class, expiry_date, supplier, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [(*r, c) for r, c in zip(reagents, categories)],
    )
    set_setting(conn, "demo_records", "true")
    fixes = [
        ("E-104", "HPLC system", "Pump stops with high pressure error", "high pressure, back-pressure, overpressure, pump stopped, blocked, clogged",
         "Blocked inline filter frit, fouled guard column or buffer precipitation", "Disconnect the column and run at 1 mL/min. If pressure stays above 20 bar replace the inline frit; otherwise back-flush or replace the guard column. Flush with warm water before organic solvent.",
         "SOP-HPLC-004 HPLC Operation and Troubleshooting", 3),
        (None, "HPLC system", "Noisy or drifting baseline", "baseline noise, drift, bubbles, lamp, spikes",
         "Air in detector flow cell or ageing deuterium lamp", "Purge the pump, flush the flow cell with isopropanol and check lamp hours; replace the lamp after 2000 h.",
         "SOP-HPLC-004 HPLC Operation and Troubleshooting", 3),
        ("IMB-01", "Benchtop centrifuge", "Run stops with imbalance error and vibration", "imbalance, vibration, wobble, shaking, unbalanced, stops",
         "Unequal tube masses or asymmetric loading", "Wait for full stop, reweigh tubes to within 0.1 g, load symmetrically and restart. Tag out if it repeats with a balanced load.",
         "SOP-CEN-002 Benchtop Centrifuge Operation", 1),
        ("LID-12", "Benchtop centrifuge", "Lid not latched error, run will not start", "lid, latch, door, will not start, interlock",
         "Lid not fully latched or faulty latch sensor", "Press the lid firmly at the centre until it clicks. Never override the interlock; request service if it persists.",
         "SOP-CEN-002 Benchtop Centrifuge Operation", 2),
        (None, "Cell culture", "Medium cloudy or turned yellow quickly", "cloudy, turbid, yellow, contamination, particles, filaments, ph drop",
         "Possible microbial contamination (requires testing to confirm)", "Quarantine the flask, disinfect the cabinet with 70% ethanol then 10% bleach, submit for mycoplasma PCR and sterility testing and notify the culture lead.",
         "SOP-CC-011 Mammalian Cell Culture: Passaging HEK293 Cells", 3),
        (None, "Cell culture", "Cells not detaching after trypsin", "not detaching, attached, trypsin, slow detachment",
         "Residual serum or calcium inhibiting trypsin, or degraded trypsin", "Rinse with Ca/Mg-free PBS before trypsin, use a fresh aliquot and incubate 3-5 min at 37 C.",
         "SOP-CC-011 Mammalian Cell Culture: Passaging HEK293 Cells", 2),
        (None, "qPCR", "Late Ct values or low efficiency", "late ct, high ct, low efficiency, inhibition, delayed amplification",
         "PCR inhibitors carried over from extraction or degraded master mix", "Run a template dilution series to detect inhibition, re-purify the template and check master mix expiry.",
         None, None),
    ]
    conn.executemany(
        "INSERT INTO troubleshooting (error_code, equipment, symptom, keywords, probable_cause, fix, source_document, source_page) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", fixes,
    )
    conn.executemany(
        "INSERT INTO profiles (name, role, title, expertise, avatar_color) VALUES (?, ?, ?, ?, ?)",
        [("Dr. Amara Okafor", "PI", "Principal Investigator", "Bioprocess development, cell line engineering", "#10b981"),
         ("Jordan Lee", "Scientist", "Senior Scientist", "Analytical chemistry, HPLC method validation", "#3b82f6"),
         ("Priya Raman", "Scientist", "Research Associate", "Cell culture, qPCR", "#a855f7"),
         ("Sam Novak", "QA", "QA Reviewer", "GLP compliance, document control", "#f59e0b")],
    )
    conn.executemany(
        "INSERT INTO projects (name, description, owner_id) VALUES (?, ?, ?)",
        [("Recombinant mAb expression", "Optimise transient HEK293 expression of candidate antibody AB-17.", 1),
         ("Impurity method validation", "Validate the RP-HPLC related-substances method for API batch release.", 2)],
    )
    conn.execute(
        "INSERT INTO experiments (project_id, title, objective, protocol_markdown, status, progress, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, "PEI:DNA ratio screen", "Determine the PEI:DNA ratio giving the highest AB-17 titre at day 5.",
         "## Protocol\n1. Seed HEK293 at $2 \\times 10^6$ cells/mL.\n2. Prepare PEI:DNA complexes at 1:1, 1:2, 1:3 and 1:4.\n"
         "3. Transfect, then shift to 32 °C after 24 h.\n4. Harvest supernatant on day 5 and quantify titre by Protein A HPLC.",
         "in_review", 60, 3),
    )
    conn.execute(
        "INSERT INTO experiments (project_id, title, objective, protocol_markdown, status, progress, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (2, "Linearity and range", "Demonstrate linearity of impurity B from LOQ to 150% of specification.",
         "## Protocol\n1. Prepare 6 calibration levels.\n2. Inject each level in triplicate.\n3. Fit $y = mx + c$ and report $R^2$.",
         "draft", 20, 2),
    )
    conn.executemany(
        "INSERT INTO experiment_steps (experiment_id, position, text, done) VALUES (?, ?, ?, ?)",
        [(1, 1, "Seed cells and confirm viability above 90%", 1), (1, 2, "Prepare PEI:DNA complexes", 1),
         (1, 3, "Transfect and record time", 1), (1, 4, "Temperature shift at 24 h", 0), (1, 5, "Harvest and quantify titre", 0),
         (2, 1, "Prepare stock and dilutions", 1), (2, 2, "Run calibration sequence", 0), (2, 3, "Regression analysis", 0)],
    )
    conn.executemany(
        "INSERT INTO experiment_variables (experiment_id, name, value, unit, kind) VALUES (?, ?, ?, ?, ?)",
        [(1, "PEI:DNA ratio", "1:1-1:4", None, "independent"), (1, "Seeding density", "2e6", "cells/mL", "controlled"),
         (1, "Titre", "pending", "mg/L", "dependent"), (2, "Concentration", "0.05-1.5", "µg/mL", "independent")],
    )
    conn.executemany(
        "INSERT INTO reviews (experiment_id, checkpoint, reviewer_id, status, notes) VALUES (?, ?, ?, ?, ?)",
        [(1, "Protocol approval", 1, "approved", "Ratios and controls look good."),
         (1, "Safety review", 4, "pending", None), (1, "Data review", 1, "pending", None)],
    )
    conn.execute(
        "INSERT INTO datasets (project_id, experiment_id, name, description, columns_json, rows_json) VALUES (?, ?, ?, ?, ?, ?)",
        (1, 1, "Titre by PEI ratio", "Day-5 titres from the PEI:DNA screen (triplicate flasks).",
         json.dumps(["sample", "ratio", "replicate", "titre_mg_l", "viability_pct"]),
         json.dumps([{"sample": f"S{i + 1}", "ratio": ratio, "replicate": rep, "titre_mg_l": t, "viability_pct": v}
                     for i, (ratio, rep, t, v) in enumerate([
                         ("1:1", 1, 42.1, 91), ("1:1", 2, 39.8, 90), ("1:1", 3, 44.0, 92),
                         ("1:2", 1, 61.5, 89), ("1:2", 2, 58.9, 90), ("1:2", 3, 63.2, 88),
                         ("1:3", 1, 84.7, 86), ("1:3", 2, 88.1, 87), ("1:3", 3, 81.9, 85),
                         ("1:4", 1, 70.3, 78), ("1:4", 2, 66.8, 76), ("1:4", 3, 72.5, 79)])])),
    )
    conn.execute(
        "INSERT INTO datasets (project_id, experiment_id, name, description, columns_json, rows_json) VALUES (?, ?, ?, ?, ?, ?)",
        (2, 2, "Impurity B calibration", "Peak area versus concentration.",
         json.dumps(["level", "conc_ug_ml", "area_mean", "area_rsd_pct"]),
         json.dumps([{"level": i + 1, "conc_ug_ml": c, "area_mean": a, "area_rsd_pct": r} for i, (c, a, r) in enumerate([
             (0.05, 1210, 3.1), (0.25, 6080, 1.8), (0.5, 12150, 1.2), (0.75, 18320, 0.9), (1.0, 24410, 0.8), (1.5, 36590, 0.7)])])),
    )
    conn.executemany(
        "INSERT INTO comments (entity_type, entity_id, parent_id, author_id, body) VALUES (?, ?, ?, ?, ?)",
        [("experiment", 1, None, 1, "Can we add a mock-transfection control?"),
         ("experiment", 1, 1, 3, "Added as flask C0 - will include in the data review."),
         ("experiment", 1, None, 4, "Please attach the BSC certification before the safety review.")],
    )
    equipment = [
        ("Analytical HPLC #2", "Lab 2.14, bench 3", "Chromatography", "Quaternary-pump RP-HPLC with DAD detector.",
         ["Check mobile phase levels and waste capacity", "Purge each channel 3 min at 5 mL/min", "Equilibrate 10 column volumes", "Run system suitability injection"],
         "Flammable mobile phases; never open fittings under pressure.", "SOP-HPLC-004", 22, 30),
        ("Benchtop centrifuge", "Lab 2.14, bench 1", "Sample prep", "Refrigerated benchtop centrifuge, swing-bucket rotor.",
         ["Inspect buckets for cracks", "Balance tubes within 0.1 g", "Close lid until it clicks", "Select program and start"],
         "Never override the lid interlock. Use sealed buckets for biological samples.", "SOP-CEN-002", 70, 28),
        ("Class II biosafety cabinet", "Tissue culture suite", "Cell culture", "Class II A2 cabinet for BSL-2 work.",
         ["Switch on and purge 5 min", "Wipe surfaces with 70% ethanol", "Keep the front grille clear", "UV is not a substitute for disinfection"],
         "Check airflow alarm status before starting work.", "SOP-CC-011", 45, 68),
        ("CO2 incubator", "Tissue culture suite", "Cell culture", "37 C, 5% CO2 humidified incubator.",
         ["Verify temperature and CO2 readings", "Check water pan level", "Minimise door-open time"], "Report alarms to the culture lead.", "SOP-CC-011", 78, 70),
        ("Eyewash and safety shower", "Corridor by Lab 2.14", "Safety", "Plumbed eyewash and drench shower.",
         ["Know the route - reachable within 10 seconds", "Hold eyelids open and flush 15 minutes", "Weekly activation test"], "Keep the access path clear at all times.", "SOP-SAF-001", 10, 80),
    ]
    conn.executemany(
        "INSERT INTO equipment (name, location, category, description, training_steps_json, safety_notes, sop_reference, tour_x, tour_y) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [(n, l, c, d, json.dumps(s), sn, ref, x, y) for n, l, c, d, s, sn, ref, x, y in equipment],
    )
    conn.commit()
    logger.info("Seeded demo records.")


if __name__ == "__main__":  # python -m app.seed <dir>: write the co-pilot demo SOP PDFs
    import sys

    for written in write_demo_sop_pdfs(Path(sys.argv[1] if len(sys.argv) > 1 else "../sample_data/sops")):
        print(written)
