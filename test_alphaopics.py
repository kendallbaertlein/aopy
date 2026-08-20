"""
Comprehensive test suite for alphaopics module
Tests all functions with various inputs and edge cases
"""

import numpy as np
import pandas as pd
import alphaopics as ao

def test_photonenergy():
    """Test photonenergy function"""
    print("\n" + "="*60)
    print("TEST 1: photonenergy()")
    print("="*60)
    
    # Test scalar
    E = ao.photonenergy(450)
    assert isinstance(E, (float, np.ndarray)), "Should return numeric value"
    assert E > 0, "Photon energy should be positive"
    print(f"[OK] Scalar input: 450 nm -> {E:.3e} J")
    
    # Test array
    wl = np.array([300, 450, 555, 700, 800])
    E = ao.photonenergy(wl)
    assert len(E) == len(wl), "Output length should match input"
    assert np.all(E > 0), "All energies should be positive"
    assert np.all(np.diff(E) < 0), "Energy should decrease with wavelength"
    print(f"[OK] Array input: {len(wl)} wavelengths - all positive, decreasing")
    
    # Test list
    E = ao.photonenergy([400, 500])
    assert len(E) == 2, "Should handle list input"
    print(f"[OK] List input: [400, 500] nm")
    
    print("[PASS] photonenergy() passed all tests")


def test_govardovskii():
    """Test Govardovskii visual pigment template"""
    print("\n" + "="*60)
    print("TEST 2: govardovskii()")
    print("="*60)
    
    # Test basic template
    wl = np.arange(300, 801)
    sensitivity = ao.govardovskii(480, wl)
    
    assert len(sensitivity) == len(wl), "Output should match wavelength array"
    assert np.max(sensitivity) <= 1.0, "Normalized sensitivity should be ≤ 1"
    assert np.max(sensitivity) > 0.99, "Peak should be near 1 (normalized)"
    assert sensitivity[180] > 0.99, "Peak should be near 480 nm (index ~180)"
    print(f"[OK] Lmax=480 nm: peak={np.max(sensitivity):.4f} at wl={wl[np.argmax(sensitivity)]}")
    
    # Test different lambda_max values
    for lmax in [380, 480, 520, 620]:
        sens = ao.govardovskii(lmax, np.arange(300, 801))
        peak_wl = np.arange(300, 801)[np.argmax(sens)]
        print(f"[OK] Lmax={lmax} nm: actual peak at ~{peak_wl} nm")
    
    print("[PASS] govardovskii() passed all tests")


def test_vlambda():
    """Test photopic illuminance calculation"""
    print("\n" + "="*60)
    print("TEST 3: vlambda()")
    print("="*60)
    
    # Create a Gaussian spectrum centered at 555 nm (peak of V(λ))
    wl = np.arange(300, 801)
    power_555 = np.exp(-((wl - 555) / 50) ** 2)
    lux_555 = ao.vlambda(power_555, wl)
    
    # Create a Gaussian spectrum centered at 400 nm (blue light, less efficient)
    power_400 = np.exp(-((wl - 400) / 50) ** 2)
    lux_400 = ao.vlambda(power_400, wl)
    
    assert lux_555 > 0, "Illuminance should be positive"
    assert lux_400 > 0, "Illuminance should be positive"
    assert lux_555 > lux_400, "Green light should be more efficient than blue"
    
    print(f"[OK] Illuminance at 555 nm (peak): {lux_555:.2f} lux")
    print(f"[OK] Illuminance at 400 nm (blue): {lux_400:.2f} lux")
    print(f"[OK] Ratio (555/400): {lux_555/lux_400:.2f}x (photopic vision favors green)")
    
    print("[PASS] vlambda() passed all tests")


def test_blambda():
    """Test biological light detection (Ba, Bp, Be)"""
    print("\n" + "="*60)
    print("TEST 4: blambda()")
    print("="*60)
    
    wl = np.arange(300, 801)
    power = np.exp(-((wl - 480) / 100) ** 2)
    
    # Test luminous quantity
    result_lum = ao.blambda(power, wl, quantity="luminous")
    assert 'Ba' in result_lum and 'Bp' in result_lum and 'Be' in result_lum
    assert result_lum['Ba'] > 0 and result_lum['Bp'] > 0 and result_lum['Be'] > 0
    print(f"[OK] Luminous: Ba={result_lum['Ba']:.2f}, Bp={result_lum['Bp']:.2f}, Be={result_lum['Be']:.2f}")
    
    # Test radiant quantity
    result_rad = ao.blambda(power, wl, quantity="radiant")
    assert result_rad['Ba'] > 0 and result_rad['Bp'] > 0
    print(f"[OK] Radiant: Ba={result_rad['Ba']:.4f}, Bp={result_rad['Bp']:.4f}")
    
    # Test photon quantity
    result_phot = ao.blambda(power, wl, quantity="photon")
    assert isinstance(result_phot['Ba'], (float, np.floating))
    print(f"[OK] Photon: Ba={result_phot['Ba']:.4f}, Bp={result_phot['Bp']:.4f}")
    
    # Test invalid quantity
    try:
        ao.blambda(power, wl, quantity="invalid")
        assert False, "Should raise ValueError for invalid quantity"
    except ValueError as e:
        print(f"[OK] Correctly raises error for invalid quantity: {str(e)[:50]}...")
    
    print("[PASS] blambda() passed all tests")


def test_aopicspecies():
    """Test species information retrieval"""
    print("\n" + "="*60)
    print("TEST 5: aopicspecies()")
    print("="*60)
    
    species = ao.aopicspecies()
    
    assert isinstance(species, pd.DataFrame), "Should return DataFrame"
    assert len(species) == 64, "Should return 64 species"
    assert 'species' in species.columns, "Should have 'species' column"
    assert 'order' in species.columns, "Should have 'order' column"
    assert 'family' in species.columns, "Should have 'family' column"
    
    print(f"[OK] Retrieved {len(species)} species")
    print(f"[OK] Columns: {list(species.columns)}")
    print(f"[OK] Sample species:")
    for i in [0, 31, 63]:
        sp = species.iloc[i]
        print(f"  - {sp['species']} ({sp['species_latin_name']})")
    
    print("[PASS] aopicspecies() passed all tests")


def test_generateaopicactionspec():
    """Test action spectrum generation"""
    print("\n" + "="*60)
    print("TEST 6: generateaopicactionspec()")
    print("="*60)
    
    # Test with numeric lmax
    spec = ao.generateaopicactionspec(opsin="Mel", lmax=480, pfilter=0)
    
    assert 'opsin' in spec, "Should have 'opsin' key"
    assert 'wavelen' in spec, "Should have 'wavelen' key"
    assert 'aspecp' in spec, "Should have 'aspecp' key"
    assert 'aspec' in spec, "Should have 'aspec' key"
    assert 'trans' in spec, "Should have 'trans' key"
    assert 'kavD65' in spec, "Should have 'kavD65' key"
    
    assert len(spec['wavelen']) == 501, "Default range should be 300-800 nm"
    assert np.max(spec['aspecp']) <= 1.0, "aspecp should be normalized"
    assert np.max(spec['aspec']) <= 1.0, "aspec should be normalized"
    
    print(f"[OK] Mel opsin (480 nm): max aspecp={np.max(spec['aspecp']):.4f}")
    print(f"[OK] Wavelength range: {spec['wavelen'][0]}-{spec['wavelen'][-1]} nm")
    print(f"[OK] Transmission: min={np.min(spec['trans']):.1f}%, max={np.max(spec['trans']):.1f}%")
    
    # Test different opsins
    for opsin_name in ["Rod", "Mel", "Scone", "Mcone", "Lcone"]:
        spec = ao.generateaopicactionspec(opsin=opsin_name, lmax=480)
        print(f"[OK] Generated spectrum for {opsin_name}")
    
    # Test custom wavelength range
    spec_custom = ao.generateaopicactionspec(
        opsin="Mel", lmax=480, range_wl=np.arange(350, 750)
    )
    assert len(spec_custom['wavelen']) == 400, "Custom range size should match"
    print(f"[OK] Custom range (350-750 nm): {len(spec_custom['wavelen'])} wavelengths")
    
    print("[PASS] generateaopicactionspec() passed all tests")


def test_alphaopic():
    """Test main alpha-opic calculation function"""
    print("\n" + "="*60)
    print("TEST 7: alphaopic()")
    print("="*60)
    
    # Create test spectrum
    wl = np.arange(300, 801)
    power = np.exp(-((wl - 480) / 50) ** 2)  # Gaussian centered at 480 nm
    
    # Basic calculation
    result = ao.alphaopic(power, wl, opsin="Mel", lmax=480, pfilter=0)
    
    assert 'Luminous' in result, "Should have 'Luminous' key"
    assert 'Radiant' in result, "Should have 'Radiant' key"
    assert 'Photon' in result, "Should have 'Photon' key"
    
    assert result['Luminous'] > 0, "Luminous should be positive"
    assert result['Radiant'] > 0, "Radiant should be positive"
    assert isinstance(result['Photon'], (float, np.floating)), "Photon should be numeric"
    
    print(f"[OK] Mel (480 nm): Luminous={result['Luminous']:.4f}, Radiant={result['Radiant']:.4f}, Photon={result['Photon']:.4f}")
    
    # Test different opsins - should have different sensitivities (using opsin-specific defaults)
    results = {}
    for opsin in ["Rod", "Mel", "Scone", "Mcone", "Lcone"]:
        r = ao.alphaopic(power, wl, opsin=opsin)  # No lmax specified - uses opsin default
        results[opsin] = r['Radiant']
        print(f"[OK] {opsin}: Radiant={r['Radiant']:.4f}")
    
    # Verify different opsins produce different results
    radiant_values = list(results.values())
    assert len(set([round(v, 4) for v in radiant_values])) > 1, "Different opsins should produce different radiant values"
    print(f"[OK] Different opsins produce different results [OK]")
    
    # Test with lens filtering
    result_filtered = ao.alphaopic(power, wl, opsin="Rod", lmax=500, pfilter=0)
    print(f"[OK] Rod with lens filter (pfilter=0): Radiant={result_filtered['Radiant']:.4f}")
    
    # Test input validation
    try:
        ao.alphaopic([1, 2, 3], [1, 2])  # Mismatched lengths
        assert False, "Should raise ValueError for mismatched input lengths"
    except ValueError as e:
        print(f"[OK] Correctly raises error for mismatched arrays: {str(e)}")
    
    print("[PASS] alphaopic() passed all tests")


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("TEST 8: Edge Cases")
    print("="*60)
    
    # Single wavelength
    E = ao.photonenergy(550)
    assert isinstance(E, (float, np.ndarray)), "Should handle single wavelength"
    print(f"[OK] Single wavelength: 550 nm -> {E:.3e} J")
    
    # Very low power
    wl = np.arange(300, 801)
    power = np.ones(len(wl)) * 1e-6
    result = ao.alphaopic(power, wl)
    assert result['Luminous'] >= 0, "Should handle very low power"
    print(f"[OK] Very low power (1e-6): Luminous={result['Luminous']:.6f}")
    
    # High power
    power = np.ones(len(wl)) * 100
    result = ao.alphaopic(power, wl)
    assert result['Luminous'] > 0, "Should handle high power"
    print(f"[OK] High power (100): Luminous={result['Luminous']:.2f}")
    
    # Zero power (all zeros)
    power = np.zeros(len(wl))
    result = ao.alphaopic(power, wl)
    assert result['Luminous'] == 0, "Zero power should give zero result"
    print(f"[OK] Zero power: Luminous={result['Luminous']}")
    
    print("[PASS] Edge cases passed all tests")


def test_consistency():
    """Test consistency across different calls"""
    print("\n" + "="*60)
    print("TEST 9: Consistency")
    print("="*60)
    
    wl = np.arange(300, 801)
    power = np.exp(-((wl - 480) / 50) ** 2)
    
    # Multiple calls should give same result (test caching)
    result1 = ao.alphaopic(power, wl, opsin="Mel", lmax=480)
    result2 = ao.alphaopic(power, wl, opsin="Mel", lmax=480)
    
    assert result1['Luminous'] == result2['Luminous'], "Results should be identical"
    assert result1['Radiant'] == result2['Radiant'], "Results should be identical"
    
    print(f"[OK] Repeated calls give identical results")
    print(f"  First call:  Luminous={result1['Luminous']:.6f}")
    print(f"  Second call: Luminous={result2['Luminous']:.6f}")
    
    print("[PASS] Consistency tests passed")


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# ALPHAOPICS COMPREHENSIVE TEST SUITE")
    print("#"*60)
    
    try:
        test_photonenergy()
        test_govardovskii()
        test_vlambda()
        test_blambda()
        test_aopicspecies()
        test_generateaopicactionspec()
        test_alphaopic()
        test_edge_cases()
        test_consistency()
        
        print("\n" + "#"*60)
        print("# [PASS] ALL TESTS PASSED SUCCESSFULLY!")
        print("#"*60 + "\n")
        
    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
