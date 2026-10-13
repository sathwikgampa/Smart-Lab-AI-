# Sample Lab Data & Documents

This directory contains ready-to-use sample datasets and laboratory standard operating procedure (SOP) PDFs to test and demonstrate **SmartLab AI**.

---

## 📁 Directory Overview

```
sample_data/
├── datasets/                 # Tabular CSV & Parquet experimental datasets
│   ├── enzyme_kinetics.csv
│   ├── cell_viability_dose_response.csv
│   ├── qpcr_gene_expression.csv
│   ├── chemistry_dataset_standardized.parquet
│   └── train-00000-of-00001.parquet
├── images/apparatus/         # 459 Lab apparatus & glassware photos (Roboflow detection)
│   └── (Beakers, flasks, balances, pipettes, cylinders, burners, etc.)
└── sops/                     # Standard Operating Procedure (SOP) PDFs
    ├── SOP-HPLC-004_HPLC_Operation_and_Troubleshooting.pdf
    ├── SOP-CC-011_Mammalian_Cell_Culture.pdf
    ├── SOP-CEN-002_Benchtop_Centrifuge.pdf
    └── SOP-SAF-001_Chemical_Spill_and_Exposure.pdf
```

---

## 📷 3. Laboratory Apparatus Images (`images/apparatus/`)

### How to use:
1. Open the SmartLab AI web interface (`http://localhost:5173`).
2. On **Ask SmartLab**, click the **Analyze image** button (or drag & drop any image from `sample_data/images/apparatus/`).
3. SmartLab AI analyzes the apparatus, glassware type, and experimental setup using the vision pipeline.

**25 Supported Lab Apparatus Classes:**
`Beaker`, `Buchner_Funnel`, `Burette_Stands`, `Calorimeter`, `Conical_Flask`, `Funnel`, `Glass_Rod`, `Measuring_Cylinder`, `Mechanical_Balance_Scale`, `Nessler_Reagent_Bottle`, `Pipette`, `Porcelain_Mortar_Pestle`, `Precision_Weight_Scale`, `Reagent_Bottle`, `Round_Bottom_Flask`, `Separating_Funnel`, `Spirit_Lamp`, `TestTube_Holder`, `Test_Tube`, `Volumetric_Flask`, `Volumetric_Pipet`, `Wash_Bottle`, `Weighing_Bottle`.


---

## 🧪 1. Experimental Datasets (`datasets/`)

### How to use:
1. Open the SmartLab AI web interface (`http://localhost:5173`).
2. Go to **Data analysis** in the sidebar (`#/data`).
3. Click **Upload CSV** and select any of the following files:

| File | Assay Type | Features Demonstrated |
|---|---|---|
| `enzyme_kinetics.csv` | Michaelis-Menten Kinetics | Substrate vs. velocity curves, inhibitor concentration impact, automatic summary stats. |
| `cell_viability_dose_response.csv` | 4PL Drug Screening | Staurosporine & Doxorubicin dose curves, viability percentages, scatter plot rendering. |
| `qpcr_gene_expression.csv` | RT-qPCR Gene Expression | Ct values for housekeeping (GAPDH/ACTB) vs. inflammatory markers (IL6/TNFa), fold change calculations. |

---

## 📄 2. Laboratory SOP PDFs (`sops/`)

### How to use:
1. Open the SmartLab AI web interface (`http://localhost:5173`).
2. Go to **Documents** (`#/documents`) or **Ask SmartLab** (`#/ask`).
3. Upload any of the PDFs to test:
   - **Page-level citations**: Questions will cite the exact page and display verbatim highlighted text in the Evidence Panel.
   - **Document Versioning**: Uploading `SOP-CC-011_v1_Mammalian_Cell_Culture.pdf` demonstrates version governance and approval status warnings.
   - **Equipment Troubleshooting**: Ask about *"HPLC Error E-104"* or *"centrifuge rotor imbalance"* to see exact diagnostic matching.

---

## 🔒 Security & Git Notice
These sample files contain no proprietary or sensitive data and are safe to commit and push to public GitHub repositories for hackathon evaluation.
