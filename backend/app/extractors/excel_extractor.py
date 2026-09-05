import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List

ID_KEYWORD_REGEX = r'(?:id|code|zip|postal|hsn|sac|gstin|asin|sku|phone|mobile|fax|year|index|seq|number\b)'

def is_identifier_column(col_name: str) -> bool:
    """Detects if a column is an ID/Code/Postal/Index column rather than a quantitative measurement."""
    c_lower = col_name.lower().strip()
    if re.search(ID_KEYWORD_REGEX, c_lower):
        # Exception for explicit count or amount columns
        if any(kw in c_lower for kw in ['amount', 'total', 'tax', 'rate', 'price', 'fee', 'qty', 'quantity', 'count']):
            return False
        return True
    return False

def extract_excel(file_path: str, filename: str = "file.xlsx") -> Dict[str, Any]:
    """
    Extracts and profiles Excel/CSV tabular files intelligently.
    Distinguishes quantitative metrics (sums, averages) from identifier/categorical fields.
    Renders clean Markdown tables for LLM digestion and fallback summaries.
    """
    ext = filename.split('.')[-1].lower()
    sheet_data = {}
    tabular_stats = {}
    summary_parts = []
    
    try:
        if ext in ['csv', 'tsv']:
            sep = '\t' if ext == 'tsv' else ','
            df = pd.read_csv(file_path, sep=sep)
            sheet_data['Sheet1'] = df
        else:
            excel_file = pd.ExcelFile(file_path)
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheet_data[sheet_name] = df
                
        for sheet_name, df in sheet_data.items():
            rows, cols = df.shape
            col_names = [str(c).strip() for c in df.columns]
            df.columns = col_names
            col_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
            missing_count = df.isnull().sum().to_dict()
            
            # Separate numeric columns into Quantitative Metrics vs Identifiers
            all_numeric_cols = df.select_dtypes(include=[np.number]).columns
            quantitative_cols = [c for c in all_numeric_cols if not is_identifier_column(c)]
            identifier_cols = [c for c in col_names if is_identifier_column(c) or c not in quantitative_cols]
            
            numeric_stats = {}
            totals_summary = {}
            for col in quantitative_cols:
                series = df[col].dropna()
                if not series.empty:
                    col_sum = float(round(series.sum(), 2))
                    col_min = float(round(series.min(), 2))
                    col_max = float(round(series.max(), 2))
                    col_mean = float(round(series.mean(), 2))
                    col_median = float(round(series.median(), 2))
                    
                    numeric_stats[col] = {
                        "sum": col_sum,
                        "min": col_min,
                        "max": col_max,
                        "mean": col_mean,
                        "median": col_median,
                    }
                    totals_summary[col] = col_sum

            # Categorical & Identifier column profiles
            categorical_stats = {}
            for col in identifier_cols[:15]:
                series = df[col].dropna().astype(str)
                if not series.empty:
                    unique_count = int(series.nunique())
                    top_samples = list(series.unique()[:3])
                    categorical_stats[col] = {
                        "unique_count": unique_count,
                        "sample_values": top_samples
                    }

            # Select key columns for clean sample preview table (max 8 columns for readability)
            key_preview_cols = []
            for col in col_names:
                c_low = col.lower()
                if any(kw in c_low for kw in ['invoice', 'order', 'date', 'type', 'item', 'description', 'qty', 'amount', 'total', 'tax', 'state', 'city']):
                    key_preview_cols.append(col)
            if not key_preview_cols:
                key_preview_cols = col_names[:8]
            else:
                key_preview_cols = key_preview_cols[:8]

            preview_df = df[key_preview_cols].head(5).fillna("")

            sample_head_dict = df.head(5).fillna("").astype(str).to_dict(orient='records')
            
            stats_entry = {
                "sheet_name": sheet_name,
                "rows_count": rows,
                "columns_count": cols,
                "columns": col_names,
                "column_types": col_types,
                "missing_values": missing_count,
                "numeric_stats": numeric_stats,
                "totals_summary": totals_summary,
                "categorical_stats": categorical_stats,
                "sample_head": sample_head_dict
            }
            tabular_stats[sheet_name] = stats_entry
            
            # Construct human-readable & LLM-friendly Sheet Summary Text
            sheet_text = f"=== Spreadsheet Sheet: '{sheet_name}' ===\n"
            sheet_text += f"Dimensions: {rows} total rows x {cols} columns\n"
            sheet_text += f"Column Directory: {', '.join(col_names[:25])}" + (f" ... (+{cols-25} more)" if cols > 25 else "") + "\n\n"
            
            if totals_summary:
                sheet_text += "Financial & Quantitative Totals (Aggregations):\n"
                for c_name, c_sum in totals_summary.items():
                    c_mean = numeric_stats[c_name]["mean"]
                    sheet_text += f"  - **{c_name}**: Total Sum = {c_sum:,.2f} | Average = {c_mean:,.2f} | Range = [{numeric_stats[c_name]['min']} to {numeric_stats[c_name]['max']}]\n"
                sheet_text += "\n"

            if categorical_stats:
                sheet_text += "Key Category & Identifier Directory:\n"
                for c_name, c_info in list(categorical_stats.items())[:6]:
                    samples_str = ", ".join(c_info["sample_values"])
                    sheet_text += f"  - **{c_name}**: {c_info['unique_count']} unique values (Samples: {samples_str})\n"
                sheet_text += "\n"

            sheet_text += "Sample Top Rows Preview:\n"
            # Render clean Markdown Table instead of raw python dicts
            header_row = "| " + " | ".join(key_preview_cols) + " |"
            sep_row = "| " + " | ".join(["---"] * len(key_preview_cols)) + " |"
            data_rows = []
            for _, row in preview_df.iterrows():
                row_vals = [str(row[c]).replace("\n", " ").strip()[:40] for c in key_preview_cols]
                data_rows.append("| " + " | ".join(row_vals) + " |")

            sheet_text += header_row + "\n" + sep_row + "\n" + "\n".join(data_rows) + "\n"
            summary_parts.append(sheet_text)
            
    except Exception as e:
        raise ValueError(f"Failed to process tabular file: {str(e)}")

    full_text = "\n\n".join(summary_parts)
    
    return {
        "file_type": "excel" if ext in ['xlsx', 'xls'] else "csv",
        "page_count": len(sheet_data),
        "full_text": full_text,
        "pages": [{"page_number": idx+1, "text": txt} for idx, txt in enumerate(summary_parts)],
        "is_tabular": True,
        "tabular_stats": tabular_stats
    }
