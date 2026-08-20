"""
Diagnostic script to compare Python alphaopics values across different opsins.
Run this and use the output to compare with R code.
"""

import numpy as np
import alphaopics as ao

# Test spectrum - Gaussian centered at 480nm
wl = np.arange(300, 801)
power = np.exp(-((wl - 480) / 50) ** 2)

print("=" * 70)
print("PYTHON ALPHAOPICS - OPSIN DIAGNOSTIC")
print("=" * 70)

print("\n1. DEFAULT BEHAVIOR (no lmax or pfilter specified)")
print("-" * 70)
print("Opsin      | Luminous   | Radiant   | Photon   | First Species Used")
print("-" * 70)
for opsin in ["Rod", "Mel", "Scone", "Mcone", "Lcone"]:
    result = ao.alphaopic(power, wl, opsin=opsin)
    # Determine which species was used
    import pandas as pd
    df = pd.read_csv(f'data/SensRefData_{opsin}.csv')
    first_spec = df[df['aspecp'].notna()].iloc[0]['species']
    print(f"{opsin:8} | {result['Luminous']:>10.2f} | {result['Radiant']:>8.4f} | {result['Photon']:>8.4f} | {first_spec}")

print("\n2. WITH NUMERIC lmax=480 (all should be same or very similar?)")
print("-" * 70)
print("Opsin      | Luminous   | Radiant   | Photon")
print("-" * 70)
for opsin in ["Rod", "Mel", "Scone", "Mcone", "Lcone"]:
    result = ao.alphaopic(power, wl, opsin=opsin, lmax=480, pfilter=0)
    print(f"{opsin:8} | {result['Luminous']:>10.2f} | {result['Radiant']:>8.4f} | {result['Photon']:>8.4f}")

print("\n3. WITH SPECIES NAME lmax='Human'")
print("-" * 70)
print("Opsin      | Luminous   | Radiant   | Photon")
print("-" * 70)
for opsin in ["Rod", "Mel", "Scone", "Mcone", "Lcone"]:
    try:
        result = ao.alphaopic(power, wl, opsin=opsin, lmax='Human', pfilter=0)
        print(f"{opsin:8} | {result['Luminous']:>10.2f} | {result['Radiant']:>8.4f} | {result['Photon']:>8.4f}")
    except Exception as e:
        print(f"{opsin:8} | ERROR: {str(e)[:50]}")

print("\n" + "=" * 70)
print("QUESTIONS FOR COMPARISON WITH R:")
print("=" * 70)
print("1. Do the default values above match what you see in R?")
print("2. For numeric lmax=480, should all opsins produce identical Radiant?")
print("3. For lmax='Human', should the values differ significantly?")
print("=" * 70)
