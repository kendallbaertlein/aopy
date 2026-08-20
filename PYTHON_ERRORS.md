# Python vs R Implementation Errors

## Critical Issues Found

### 1. **blambda() - Missing Spectral Functions for "radiant" and "photon" quantities** 
**Location:** [alphaopics.py](alphaopics.py#L165-L172)

**Issue:** The "radiant" and "photon" cases don't apply the Ba(λ), Bp(λ), Be(λ) spectral functions. They just return the raw sum of power, making Ba, Bp, and Be identical instead of different values based on biological sensitivity.

**R Implementation (CORRECT):**
```r
# Luminous case: Weight by function, then divide by kavD65
ba <- sum(df_merge_balam$power * df_merge_balam$balambda, na.rm = TRUE) /
  VisualStandards$balambda$kavD65  # kavD65 is a single constant per opsin

# Radiant case: Weight by function (no D65 normalization)
ba <- sum(df_merge_balam$power * df_merge_balam$balambda, na.rm = TRUE)
bp <- sum(df_merge_bplam$power * df_merge_bplam$bplambda, na.rm = TRUE)
be <- sum(df_merge_belam$power * df_merge_belam$belambda, na.rm = TRUE)

# Photon case: Weight by function, divide by energy and 10000
ba <- log10(sum(df_merge_balam$power * df_merge_balam$balambda / 
                  (photonenergy(...) * 10000), na.rm = TRUE))
```

**Python Implementation (WRONG):**
```python
# Luminous (lines 136-147): Multiplies by K_m (683) but should divide by kavD65
ba = K_m * np.sum(power * ba_interp(wavelength))  # ← Wrong normalization constant

elif quantity == "radiant":
    ba = np.sum(power)           # ← WRONG! Should apply Ba(λ) function
    bp = np.sum(power)           # ← WRONG! Should apply Bp(λ) function  
    be = np.sum(power)           # ← WRONG! Missing interpolation to wavelengths

elif quantity == "photon" (line 166-169):
    photo_energy = photonenergy(wavelength)
    ba = np.log10(np.sum(power / photo_energy) + 1e-20)
    # ← WRONG! Missing: Ba(λ), Bp(λ), Be(λ) spectral functions
    # ← WRONG! Missing: /10000 scaling
```

**Impact:** 
- "luminous" uses wrong efficacy constant (should use kavD65 from CSV files)
- "radiant" **returns identical Ba=Bp=Be** (just power sum!)
- "photon" doesn't weight by biological sensitivity at all

---

### 2. **blambda() - Wrong Luminous Normalization (kavD65 not used)**

**Issue:** The CSV files have a `kavD65` column that provides the a-opic efficacy for each opsin, but the Python code multiplies by K_m (683, photopic) instead of dividing by the opsin-specific kavD65.

**In the data:**
```
# From VisualStandards_balambda.csv
wavelen,balambda,kavD65
360,0.6976...,0.00284...  # kavD65 ≈ 0.00284 for Ba(λ) 
...
```

**Python code (Line 137):**
```python
ba = K_m * np.sum(power * ba_interp(wavelength))  # K_m = 683
```

**Should be:**
```python
ba = np.sum(power * ba_interp(wavelength)) / kavD65
# where kavD65 is read from the CSV (should be ~0.00284 for Ba)
```

**Impact:** Results will be ~240,000x too large (683 ÷ 0.00284 ≈ 240,000)!

---

### 3. **generateaopicactionspec() - Wrong kavD65 Calculation**

**R Implementation (CORRECT):**
```r
# Load D65 daylight spectrum
wl65 <- VisualStandards$D65$wavelen
sp65 <- VisualStandards$D65$spectra
sp65 <- sp65[wl65 >= range[1] & wl65 <= range[length(range)]]
kavD65 <- sum(sp65 * aspec, na.rm = TRUE) / VisualStandards$D65$lux
# kavD65 is the luminous efficacy (W/lm) for D65 daylight
```

**Python Implementation (WRONG):**
```python
# Incorrect: Simple scaling formula
kavD65 = 0.5 / np.max(aspec) if np.max(aspec) > 0 else 1.0
# ← This is completely arbitrary and doesn't use D65 data
```

**Impact:** The luminous efficacy value will be wrong, making all photopic luminance calculations incorrect.

---

### 3. **generateaopicactionspec() - Incomplete Energy Conversion Logic**

**R Implementation (CORRECT):**
```r
# Different handling based on whether lens filter is pre-applied
if (is.character(lmax)) {
    lens_filter <- SensRefData[[lmax]][[opsin]]$lens_filter
    if (lens_filter == "yes") {
        aspec <- aspecp / e  # Filter already applied to aspecp
    } else if (lens_filter == "no") {
        aspecp <- aspecp * (trans / 100)  # Apply filter first
        aspec <- aspecp / e
    }
} else {
    # For Govardovskii model, always apply filter then convert
    aspecp <- aspecp * (trans / 100)
    aspec <- aspecp / e
}
```

**Python Implementation (INCOMPLETE):**
```python
# Always applies transmission and converts the same way
# Missing the distinction between pre-filtered vs. non-filtered data
trans_fraction = trans / 100
aspecp_filtered = aspecp * trans_fraction
photo_energy = photonenergy(range_wl)
aspec = aspecp_filtered / photo_energy * np.mean(photo_energy)
# ← The "* np.mean(photo_energy)" is an extra scaling that shouldn't be there
```

---

### 4. **blambda() - Return Type Inconsistency**

**R Implementation:**
```r
# Returns a data frame
return(data.frame(
    Ba = as.numeric(ba),
    Bp = as.numeric(bp),
    Be = as.numeric(be)
))
```

**Python Implementation:**
```python
# Returns a dictionary
return {'Ba': ba, 'Bp': bp, 'Be': be}
```

**Note:** The test file expects dict-like access, which works, but it's inconsistent. The function should probably return a pandas DataFrame for consistency with `aopicspecies()`.

---

### 5. **Missing Data Loading**

**Critical Issue:** The Python version tries to load CSV files from the `data/` directory:
- `VisualStandards_vlambda.csv`
- `VisualStandards_balambda.csv`
- `VisualStandards_bplambda.csv`
- `VisualStandards_belambda.csv`

But these files likely don't exist or may be incorrectly formatted. The R version has these as built-in data objects in `VisualStandards` list.

**Impact:** If the CSV files don't exist, `vlambda()` and `blambda()` will use fallback calculations that are incorrect.

---

## Test Failures You May See

| Test | Issue | Symptom |
|------|-------|---------|
| `test_blambda()` radiant | Ba=Bp=Be (all identical) | Should be different values |
| `test_blambda()` photon | Missing spectral functions | Wrong values, no biological weighting |
| `test_alphaopic()` | Wrong kavD65 from generateaopicactionspec | Results off by orders of magnitude |
| All luminous calculations | kavD65 wrong in blambda | Results ~240,000x too large |

---

## Summary of Required Fixes

1. **Fix `blambda()` "radiant" case** (lines 165-167):
   - Apply Ba(λ), Bp(λ), Be(λ) by interpolating to wavelengths
   - Get the wavelengths that overlap with input wavelengths

2. **Fix `blambda()` "luminous" case** (lines 136-147):
   - Replace `K_m * sum(power * func)` with `sum(power * func) / kavD65`
   - Extract kavD65 from CSV files with `ba_data['kavD65'].iloc[0]`

3. **Fix `blambda()` "photon" case** (lines 169-171):
   - Apply Ba(λ), Bp(λ), Be(λ) functions by interpolating to wavelengths
   - Divide by `photonenergy(...) * 10000` (not just photonenergy)

4. **Fix `generateaopicactionspec()` kavD65** (line 320):
   - Load D65 spectrum from CSV file
   - Calculate: `kavD65 = sum(D65_spectrum * aspec_energy) / D65_lux`
   - Don't use the simplified formula `0.5 / np.max(aspec)`

5. **Fix energy conversion in `generateaopicactionspec()`** (line 316):
   - Remove the extra `* np.mean(photo_energy)` scaling
   - Should just be: `aspec = aspecp / photo_energy`

6. **Fix lens filter handling** in `generateaopicactionspec()` (around line 285):
   - Load lens_filter metadata from SensRefData CSVs when using species
   - Apply conditional logic like R does (filter before or after conversion)

