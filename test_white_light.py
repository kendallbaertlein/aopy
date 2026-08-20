"""
Test white light with Human defaults
"""

import numpy as np
import alphaopics as ao

# Test spectrum - Gaussian centered at 480nm
wl = np.arange(300, 801)
power = np.exp(-((wl - 480) / 50) ** 2)

print("=" * 70)
print("TESTING FIXED DEFAULTS (lmax='Human', pfilter='Human')")
print("=" * 70)

print("\nTest 1: Using new defaults (lmax='Human', pfilter='Human')")
print("-" * 70)
print("Opsin      | Luminous   | Radiant   | Photon")
print("-" * 70)
for opsin in ["Rod", "Mel", "Scone", "Mcone", "Lcone"]:
    result = ao.alphaopic(power, wl, opsin=opsin)
    print(f"{opsin:8} | {result['Luminous']:>10.2f} | {result['Radiant']:>8.4f} | {result['Photon']:>8.4f}")

print("\nTest 2: Comparing with user's expected white light photon values")
print("-" * 70)
print("User expected photon: 15.30, 15.41, 14.92, 15.54, 15.68")
print("Opsin      | Photon     | Expected  | Diff")
print("-" * 70)
expected = [15.30, 15.41, 14.92, 15.54, 15.68]
for i, opsin in enumerate(["Rod", "Mel", "Scone", "Mcone", "Lcone"]):
    result = ao.alphaopic(power, wl, opsin=opsin)
    diff = result['Photon'] - expected[i]
    print(f"{opsin:8} | {result['Photon']:>10.2f} | {expected[i]:>9.2f} | {diff:>7.2f}")

print()
