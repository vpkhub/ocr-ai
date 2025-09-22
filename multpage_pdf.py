# COMMAND ----------
# Install required libraries (Databricks cluster)
# You may need to restart the cluster after install

%pip install pdf2image llama-index openai pandas poppler-utils

# COMMAND ----------
# Imports

from pdf2image import convert_from_path
from llama_index.core.llms import ChatMessage
from llama_index.core.schema import ImageBlock
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
import pandas as pd
import json
import os

# COMMAND ----------
# Set up OpenAI key (store securely in Databricks secrets!)
import os
os.environ["OPENAI_API_KEY"] = dbutils.secrets.get("openai", "api-key")  
# Make sure you have stored your key in Databricks secrets under scope "openai"

# COMMAND ----------
# Upload your transcript.pdf file to Databricks FileStore or DBFS
# Example path: /dbfs/FileStore/transcript.pdf
pdf_file = "/dbfs/FileStore/transcript.pdf"

# Convert PDF to images
pages = convert_from_path(pdf_file)
image_files = []

for i, page in enumerate(pages):
    filename = f"/dbfs/FileStore/page_{i}.png"
    page.save(filename, "PNG")
    image_files.append(filename)

print(f"Converted {len(image_files)} pages to images")

# COMMAND ----------
# Initialize multimodal LLM
llm = OpenAIMultiModal(model="gpt-4o-mini")  # or gpt-4.1 if enabled

# COMMAND ----------
# Extract transcript data page by page
all_results = []

for img_file in image_files:
    with open(img_file, "rb") as f:
        img_block = ImageBlock(image=f)

        message = ChatMessage(
            role="user",
            blocks=[
                img_block,
                "Extract all transcript data from this page. "
                "Return JSON with keys: semester, course_code, course_name, grade, gpa (if available)."
            ]
        )

        response = llm.chat(messages=[message])

    # Try parsing JSON safely
    try:
        data = json.loads(response.text)
        if isinstance(data, list):
            all_results.extend(data)
        else:
            all_results.append(data)
    except json.JSONDecodeError:
        print(f"⚠️ Could not parse JSON for {img_file}")
        print(response.text)

print("✅ Extraction complete!")

# COMMAND ----------
# Save results into DataFrame and export to Excel/CSV

if all_results:
    df = pd.DataFrame(all_results)
    output_excel = "/dbfs/FileStore/transcript_data.xlsx"
    output_csv = "/dbfs/FileStore/transcript_data.csv"
    df.to_excel(output_excel, index=False)
    df.to_csv(output_csv, index=False)
    display(df)
    print(f"Saved Excel: {output_excel}")
    print(f"Saved CSV: {output_csv}")
else:
    print("⚠️ No data extracted. Check model responses.")
