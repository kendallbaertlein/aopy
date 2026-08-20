"""
Debug Scone vs other opsins for white light spectrum
"""

import numpy as np
import pandas as pd
import alphaopics as ao

print("=" * 80)
print("DEBUGGING SCONE RADIANT VALUES")
print("=" * 80)

# Create a white light spectrum (relatively flat across visible range)
wl = np.arange(300, 801)
power_white = np.ones_like(wl, dtype=float)  # Flat spectrum

print("\n1. White Light Spectrum Test - Default Behavior (lmax=None, pfilter=None)")
print("-" * 80)
print("Opsin    | Luminous    | Radiant     | Photon    | Data Range    | First Species")
print("-" * 80)

for opsin in ["Rod", "Mel", "Scone", "Mcone", "Lcone"]:
    result = ao.alphaopic(power_white, wl, opsin=opsin)
    
    # Check what species data is being used
    sens_df = pd.read_csv(f'data/SensRefData_{opsin}.csv')
    first_species = sens_df[sens_df['aspecp'].notna()].iloc[0]
    species_name = first_species['species']
    
    # Get wavelength range for that species
    first_data = sens_df[sens_df['species'] == species_name]
    wl_range = f"{first_data['wavelen'].min()}-{first_data['wavelen'].max()}"
    
    print(f"{opsin:8} | {result['Luminous']:>11.2f} | {result['Radiant']:>11.4f} | {result['Photon']:>9.4f} | {wl_range:12} | {species_name}")

print("\n2. Checking Scone Action Spectrum Details")
print("-" * 80)

spec = ao.generateaopicactionspec(opsin="Scone", lmax=None, pfilter=None)
print(f"Opsin: {spec['opsin']}")
print(f"Wavelength range: {spec['wavelen'][0]:.0f}-{spec['wavelen'][-1]:.0f} nm (length: {len(spec['wavelen'])})")
print(f"aspecp (photon) - max: {np.max(spec['aspecp']):.6f}, non-zero count: {np.sum(spec['aspecp'] > 0)}")
print(f"aspec (energy) - max: {np.max(spec['aspec']):.6f}, non-zero count: {np.sum(spec['aspec'] > 0)}")
print(f"kavD65: {spec['kavD65']:.6f}")

# Show where the data actually is
nonzero_idx = np.where(spec['aspecp'] > 0)[0]
if len(nonzero_idx) > 0:
    print(f"Non-zero aspecp range: {spec['wavelen'][nonzero_idx[0]]:.0f}-{spec['wavelen'][nonzero_idx[-1]]:.0f} nm")
    print(f"Peak aspecp at wavelength: {spec['wavelen'][np.argmax(spec['aspecp'])]:.0f} nm")

print("\n3. Comparing with numeric lmax=480 (Govardovskii)")
print("-" * 80)

result_gov = ao.alphaopic(power_white, wl, opsin="Scone", lmax=480, pfilter=0)
spec_gov = ao.generateaopicactionspec(opsin="Scone", lmax=480, pfilter=0)

print(f"Scone with Govardovskii (lmax=480):")
print(f"  Luminous: {result_gov['Luminous']:.2f}")
print(f"  Radiant: {result_gov['Radiant']:.4f}")
print(f"  Photon: {result_gov['Photon']:.4f}")
print(f"  aspecp max: {np.max(spec_gov['aspecp']):.6f}, non-zero count: {np.sum(spec_gov['aspecp'] > 0)}")

print("\n4. Comparing with lmax='Human' (measured Human data)")
print("-" * 80)

try:
    result_human = ao.alphaopic(power_white, wl, opsin="Scone", lmax="Human", pfilter=0)
    spec_human = ao.generateaopicactionspec(opsin="Scone", lmax="Human", pfilter=0)
    
    print(f"Scone with Human sensitivities:")
    print(f"  Luminous: {result_human['Luminous']:.2f}")
    print(f"  Radiant: {result_human['Radiant']:.4f}")
    print(f"  Photon: {result_human['Photon']:.4f}")
    print(f"  aspecp max: {np.max(spec_human['aspecp']):.6f}, non-zero count: {np.sum(spec_human['aspecp'] > 0)}")
    
    # Show wavelength range
    nonzero_idx = np.where(spec_human['aspecp'] > 0)[0]
    if len(nonzero_idx) > 0:
        print(f"  Non-zero aspecp range: {spec_human['wavelen'][nonzero_idx[0]]:.0f}-{spec_human['wavelen'][nonzero_idx[-1]]:.0f} nm")
except Exception as e:
    print(f"  ERROR: {str(e)}")

print("\n5. Raw Scone Data Analysis")
print("-" * 80)

scone_data = pd.read_csv('data/SensRefData_Scone.csv')
print(f"Total rows in Scone data: {len(scone_data)}")
print(f"Columns: {list(scone_data.columns)}")
print(f"\nSpecies with non-NaN aspecp:")
for idx, row in scone_data[scone_data['aspecp'].notna()].iterrows():
    wl_data = scone_data[(scone_data['species'] == row['species']) & (scone_data['wavelen'].notna())]
    print(f"  {row['species']:20} - lmax: {row['lmax']:6.1f}, wavelengths: {wl_data['wavelen'].min():.0f}-{wl_data['wavelen'].max():.0f} nm ({len(wl_data)} points)")

print("\n" + "=" * 80)
print("DIAGNOSIS:")
print("=" * 80)
print("If Radiant values are very different between default and lmax='Human',")
print("then the issue is that default is using first species (not Human)")
print("If Radiant=0.01 even with lmax='Human', then the calculation is wrong")
print("=" * 80)
