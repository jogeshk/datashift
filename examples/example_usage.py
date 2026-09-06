import datashift

print("Starting data conversion tracking...")

# Note: Ensure you have 'dummy.json' file locally to run this successfully!
datashift.convert("genesis.json", "output.yaml")

print("Conversion completed")