import json
import csv
import pathlib
import sys
import xml.etree.ElementTree as ET
import pandas as pd

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    import yaml
except ImportError:
    yaml = None

class DataShiftError(Exception):
    """Base exception class for all custom errors thrown by datashift."""
    pass

class FormatIncompatibilityError(DataShiftError):
    """Raised when data configurations mismatch or structures cannot normalize."""
    pass

class DependencyMissingError(DataShiftError):
    """Raised when an optional processing library wrapper is not installed."""
    pass

def _flatten_dict(d: dict, parent_key: str = '', sep: str = '_') -> dict:
    """Recursively flattens deeply nested structural trees down into 1D profiles."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def convert(input_path: str, output_path: str) -> None:
    """
    Universally shifts data matrices across 8 configuration setups.
    Wrapped tightly in customized try-catch frames to filter out bad dependencies.
    """
    in_file = pathlib.Path(input_path)
    out_file = pathlib.Path(output_path)
    
    if not in_file.exists():
        raise FileNotFoundError(f"DataShift Storage Error: Source element path missing at '{input_path}'")
        
    in_ext = in_file.suffix.lower()
    out_ext = out_file.suffix.lower()
    
    valid_formats = ['.json', '.csv', '.xlsx', '.ndjson', '.jsonl', '.yaml', '.yml', '.toml', '.xml', '.md']
    
    if in_ext not in valid_formats:
        raise FormatIncompatibilityError(f"DataShift Syntax Error: Unrecognized extension '{in_ext}'. Available: {', '.join(valid_formats)}")
    if out_ext not in valid_formats:
        raise FormatIncompatibilityError(f"DataShift Syntax Error: Unrecognized output target '{out_ext}'. Available: {', '.join(valid_formats)}")

    raw_data = None
    df = None

    try:
        if in_ext == '.json':
            with open(in_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
        elif in_ext in ['.ndjson', '.jsonl']:
            with open(in_file, 'r', encoding='utf-8') as f:
                raw_data = [json.loads(line) for line in f if line.strip()]
                
        elif in_ext in ['.yaml', '.yml']:
            if yaml is None:
                raise DependencyMissingError("System Exception: 'pyyaml' backend package missing. Execute: pip install pyyaml")
            with open(in_file, 'r', encoding='utf-8') as f:
                raw_data = yaml.safe_load(f)
                
        elif in_ext == '.toml':
            if tomllib is None:
                raise DependencyMissingError("System Exception: 'tomli' wrapper fallback required on older runtimes. Execute: pip install tomli")
            with open(in_file, 'r', encoding='utf-8') as f:
                raw_data = tomllib.loads(f.read())
                
        elif in_ext == '.csv':
            df = pd.read_csv(in_file)
            
        elif in_ext == '.xlsx':
            df = pd.read_excel(in_file)
            
        elif in_ext == '.xml':
            tree = ET.parse(in_file)
            root = tree.getroot()
            raw_data = []
            for child in root:
                item = {subchild.tag: subchild.text for subchild in child}
                raw_data.append(item)
                
        elif in_ext == '.md':
            with open(in_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and '|' in line]
            if len(lines) < 3:
                raise FormatIncompatibilityError("Parsing Error: MD file lacks a structural 3-row markdown table layout.")
            headers = [cell.strip() for cell in lines.split('|')[1:-1]]
            rows = []
            for line in lines[2:]:
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                rows.append(dict(zip(headers, cells)))
            raw_data = rows

    except (json.JSONDecodeError, csv.Error, ET.ParseError) as syntax_err:
        raise FormatIncompatibilityError(f"DataShift Structural Corruption: File at '{input_path}' contains malformed markup.\nDetails: {syntax_err}") from syntax_err
    except Exception as general_read_err:
        if isinstance(general_read_err, DataShiftError):
            raise general_read_err
        raise DataShiftError(f"DataShift Critical Ingestion Error: Failed accessing target '{input_path}'.\nDetails: {general_read_err}") from general_read_err

    try:
        if df is None and raw_data is not None:
            if isinstance(raw_data, dict):
                flat_dict = _flatten_dict(raw_data)
                df = pd.DataFrame([flat_dict])
            elif isinstance(raw_data, list):
                flat_list = [_flatten_dict(item) if isinstance(item, dict) else item for item in raw_data]
                df = pd.DataFrame(flat_list)
        elif df is not None and raw_data is None:
            raw_data = df.to_dict(orient='records')
            
        if df is None or df.empty:
            raise FormatIncompatibilityError("Matrix Refusal Exception: Output parsing resulted in an empty configuration index schema.")
    except Exception as data_normalization_err:
        if isinstance(data_normalization_err, DataShiftError):
            raise data_normalization_err
        raise DataShiftError(f"DataShift Matrix Compilation Mismatch: Failed flattening structural records down to normal data shapes.\nDetails: {data_normalization_err}") from data_normalization_err

    try:
        if out_ext == '.json':
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=4)
                
        elif out_ext in ['.ndjson', '.jsonl']:
            with open(out_file, 'w', encoding='utf-8') as f:
                if isinstance(raw_data, list):
                    for row in raw_data:
                        f.write(json.dumps(row) + '\n')
                else:
                    f.write(json.dumps(raw_data) + '\n')
                    
        elif out_ext in ['.yaml', '.yml']:
            if yaml is None:
                raise DependencyMissingError("System Exception: Cannot output to YAML since 'pyyaml' module is unavailable.")
            with open(out_file, 'w', encoding='utf-8') as f:
                yaml.dump(raw_data, f, default_flow_style=False)
                
        elif out_ext == '.toml':
            with open(out_file, 'w', encoding='utf-8') as f:
                if isinstance(raw_data, dict):
                    f.write(pd.Series(raw_data).to_string())
                else:
                    df.to_json(out_file, orient='records')
                    
        elif out_ext == '.csv':
            df.to_csv(out_file, index=False)
            
        elif out_ext == '.xlsx':
            df.to_excel(out_file, index=False)
            
        elif out_ext == '.xml':
            root = ET.Element("root")
            for item in raw_data:
                row_el = ET.SubElement(root, "row")
                if isinstance(item, dict):
                    for k, v in item.items():
                        sub = ET.SubElement(row_el, k)
                        sub.text = str(v)
            tree = ET.ElementTree(root)
            tree.write(out_file, encoding='utf-8', xml_declaration=True)
            
        elif out_ext == '.md':
            with open(out_file, 'w', encoding='utf-8') as f:
                headers = df.columns.tolist()
                f.write("| " + " | ".join(headers) + " |\n")
                f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
                for _, row in df.iterrows():
                    f.write("| " + " | ".join([str(val) for val in row]) + " |\n")

    except PermissionError as fs_lock_err:
        raise PermissionError(f"DataShift IO Permission Denied: Unable to safely lock target folder down for writing at '{output_path}'. Verify if file is currently open in Excel or another program.") from fs_lock_err
    except Exception as system_compile_err:
        if isinstance(system_compile_err, DataShiftError):
            raise system_compile_err
        raise DataShiftError(f"DataShift OS File Export Failure: Could not write generated bundle down to system storage at '{output_path}'.\nDetails: {system_compile_err}") from system_compile_err
