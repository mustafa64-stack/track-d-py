import json
from pathlib import Path

file_path = Path(__file__).parent / "evaluation_test_cases.json"

with open(file_path, "r", encoding="utf-8") as file:
    data = json.load(file)

source_cases = data["source_based_cases"]
off_material_cases = data["off_material_cases"]

print("AI STUDY COMPANION — DAY 3 EVALUATION")
print("-" * 45)
print(f"Source-based test cases: {len(source_cases)}")
print(f"Off-material test cases: {len(off_material_cases)}")

print("\nSample source-based question:")
print(source_cases[0]["question"])
print("Expected answer:", source_cases[0]["expected_answer"])
print("Expected PDF page:", source_cases[0]["expected_source_page"])

print("\nSample off-material question:")
print(off_material_cases[0]["question"])
print("Expected behavior:", off_material_cases[0]["expected_behavior"])

print("\nEvaluation dataset loaded successfully!")