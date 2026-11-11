import io
import pandas as pd
from fastapi.testclient import TestClient
from main import app, clean_company_name, standardize_legal_suffixes, load_dataframe, get_file_type

client = TestClient(app)

def test_suffix_standardization():
    print("Testing suffix standardization...")
    assert standardize_legal_suffixes("PTE. LTD.") == "LTD"
    assert standardize_legal_suffixes("PT. L.T.D.") == "LTD"
    assert standardize_legal_suffixes("PRIVATE LIMITED") == "LTD"
    assert standardize_legal_suffixes("Google LLC") == "GOOGLE LLC"
    assert standardize_legal_suffixes("Tesla, Inc.") == "TESLA, INC"
    assert standardize_legal_suffixes("Microsoft Corporation") == "MICROSOFT CORP"
    print("OK: Suffix standardization tests passed.")

def test_company_name_cleaning():
    print("Testing core company name cleaning...")
    # Suffixes should be standard-mapped and then completely stripped, leaving the core alphanumeric name
    assert clean_company_name("Google LLC") == "GOOGLE"
    assert clean_company_name("Tesla, Inc.") == "TESLA"
    assert clean_company_name("Microsoft Corporation") == "MICROSOFT"
    assert clean_company_name("Standard Chartered Pte Ltd") == "STANDARDCHARTERED"
    assert clean_company_name("PT. ABC Indonesia") == "ABCINDONESIA"
    assert clean_company_name("PTE. LTD.") == ""
    assert clean_company_name("PT. L.T.D.") == ""
    assert clean_company_name("PRIVATE LIMITED") == ""
    assert clean_company_name("Company PTE. LTD.") == "COMPANY"
    assert clean_company_name("Company PT. L.T.D.") == "COMPANY"
    assert clean_company_name("Company PRIVATE LIMITED") == "COMPANY"
    assert clean_company_name("Random Entity") == "RANDOMENTITY"
    assert clean_company_name(None) == ""
    print("OK: Company name cleaning tests passed.")

def test_slicing_and_templating():
    print("Testing slicing and templating logic...")
    from main import get_column_letter
    names = [
        "International Business Machines Corporation New York",
        "Standard Chartered Bank",
        "Google Inc"
    ]
    df = pd.DataFrame({"Company Name": names})
    
    cleaned_col_name = 'Cleaned Name (exact match, no spaces/chars)'
    df[cleaned_col_name] = df["Company Name"].apply(clean_company_name)
    
    cleaned_col_idx = list(df.columns).index(cleaned_col_name) + 1
    col_letter = get_column_letter(cleaned_col_idx)
    
    df['by Left 25 Characters'] = [f"=LEFT({col_letter}{i}, 25)" for i in range(2, len(df) + 2)]
    df['by Left 15 Characters'] = [f"=LEFT({col_letter}{i}, 15)" for i in range(2, len(df) + 2)]
    df['by Left 10 Characters'] = [f"=LEFT({col_letter}{i}, 10)" for i in range(2, len(df) + 2)]
    
    # 1. IBM
    row_ibm = df.iloc[0]
    assert row_ibm[cleaned_col_name] == "INTERNATIONALBUSINESSMACHINESNEWYORK"
    assert row_ibm['by Left 25 Characters'] == "=LEFT(B2, 25)"
    assert row_ibm['by Left 15 Characters'] == "=LEFT(B2, 15)"
    assert row_ibm['by Left 10 Characters'] == "=LEFT(B2, 10)"
    
    # 2. Standard Chartered
    row_sc = df.iloc[1]
    assert row_sc[cleaned_col_name] == "STANDARDCHARTEREDBANK"
    assert row_sc['by Left 15 Characters'] == "=LEFT(B3, 15)"
    
    print("OK: Slicing and templating tests passed.")

def test_api_parse_headers():
    print("Testing /api/parse-headers endpoint...")
    csv_bytes = b"Company ID,Company Name,Website\nC01,Google LLC,google.com\n"
    response = client.post(
        "/api/parse-headers",
        files={"file": ("companies.csv", csv_bytes, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "headers" in data
    assert data["headers"] == ["Company ID", "Company Name", "Website"]
    print("OK: /api/parse-headers endpoint test passed.")

def test_api_template():
    print("Testing /api/template endpoint...")
    csv_bytes = b"Company Name,Website\nGoogle LLC,google.com\nTesla Inc,tesla.com\nGoogle LLC,google.com\n"
    
    # 1. Test with deduplicate=True
    response = client.post(
        "/api/template",
        files={"file": ("companies.csv", csv_bytes, "text/csv")},
        data={"company_col": "Company Name", "export_format": "excel", "deduplicate": "true"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "download_id" in data
    assert data["total_records"] == 2
    
    # 2. Test with deduplicate=False
    response2 = client.post(
        "/api/template",
        files={"file": ("companies.csv", csv_bytes, "text/csv")},
        data={"company_col": "Company Name", "export_format": "excel", "deduplicate": "false"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert "download_id" in data2
    assert data2["total_records"] == 3
    print("OK: /api/template endpoint test passed.")

if __name__ == "__main__":
    test_suffix_standardization()
    test_company_name_cleaning()
    test_slicing_and_templating()
    test_api_parse_headers()
    test_api_template()
    print("\nALL TEMPLATER TESTS PASSED SUCCESSFULLY!")
