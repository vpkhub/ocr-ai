import streamlit as st
import pandas as pd
import json

def normalize(text):
    if text is None:
        return ""
    return str(text).strip().lower()

def validate_doc(gt_row, ocr_doc):
    results = []
    correct_count = 0
    total_fields = 0

    # Normalize both field names and strip spaces for robust matching
    ocr_fields = {f["fieldName"].strip().lower(): f for f in ocr_doc["extractedFields"]}
    outstanding_medisave_payable = ocr_fields.get("outstanding medisave payable", {}).get("value", "")
    print(f"Outstanding MediSave Payable: {outstanding_medisave_payable}")

    for field in gt_row.index:
        if field == "document_id":
            continue  # skip ID column

        norm_field = field.strip().lower()
        gt_value = normalize(gt_row[field])
        ocr_value = normalize(ocr_fields.get(norm_field, {}).get("value", ""))

        match = gt_value == ocr_value
        confidence = ocr_fields.get(norm_field, {}).get("confidence_score", None)

        results.append({
            "field_name": field,
            "ground_truth": gt_row[field],
            "ocr_value": ocr_fields.get(norm_field, {}).get("value", ""),
            "confidence_score": confidence,
            "match": match
        })

        total_fields += 1
        if match:
            correct_count += 1

    accuracy = correct_count / total_fields if total_fields > 0 else 0
    return results, accuracy

def ocr_validation_ui():
    st.markdown("<h3 style='text-align: center; font-size:1.5rem;'>OCR Validation Dashboard (CSV/Excel + JSON)</h3>", unsafe_allow_html=True)

    gt_file = st.file_uploader("Upload Ground Truth CSV/Excel", type=["csv", "xlsx"])
    ocr_file = st.file_uploader("Upload OCR Response JSON", type=["json"])

    if gt_file and ocr_file:
        # Load ground truth
        if gt_file.name.endswith(".csv"):
            gt_df = pd.read_csv(gt_file)
        else:
            gt_df = pd.read_excel(gt_file)

        # Load OCR JSON (could be list of docs or single doc)
        ocr_data = json.load(ocr_file)
        if isinstance(ocr_data, dict):  # single doc
            ocr_data = [ocr_data]
        elif isinstance(ocr_data, list):
            pass  # already a list
        else:
            st.error("OCR response JSON must be a dict or list of dicts.")
            return

        ocr_dict = {doc["documentId"]: doc for doc in ocr_data}

        overall_results = []
        doc_accuracies = []

        # Loop over ground truth documents
        for _, row in gt_df.iterrows():
            doc_id = row["documentId"]
            if doc_id not in ocr_dict:
                continue
            results, accuracy = validate_doc(row, ocr_dict[doc_id])
            doc_accuracies.append(accuracy)
            for r in results:
                r["documentId"] = doc_id
                overall_results.append(r)

        results_df = pd.DataFrame(overall_results)

        # Show metrics and tables only if results exist
        st.subheader("Validation Metrics")
        if len(doc_accuracies) > 0:
            st.metric("Overall Accuracy", f"{sum(doc_accuracies)/len(doc_accuracies)*100:.2f}%")
        else:
            st.metric("Overall Accuracy", "N/A")

        if not results_df.empty:
            # Document-level accuracy
            doc_acc_df = results_df.groupby("documentId")["match"].mean().reset_index()
            doc_acc_df["match"] = doc_acc_df["match"] * 100
            doc_acc_df = doc_acc_df.rename(columns={"match": "accuracy (%)"})
            st.subheader("Document-level Accuracy")
            st.dataframe(doc_acc_df)

            # Field-wise accuracy
            field_acc = results_df.groupby("field_name")["match"].mean().reset_index()
            field_acc["match"] = field_acc["match"] * 100
            st.subheader("Field-wise Accuracy")
            st.dataframe(field_acc)

            # Detailed table
            st.subheader("Field-Level Comparison")
            st.dataframe(results_df)
        else:
            st.info("No matching documents found for validation.")
