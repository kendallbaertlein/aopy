"""
Alphaopics - Clean, High-Robustness Python Implementation
=========================================================
"""
import os
import sys
import warnings
import numpy as np
import pandas as pd
from scipy import interpolate

# ============================================================================
# CORE PHOTOMETRIC CONSTANTS
# ============================================================================
h = 6.62607015e-34  # Planck's constant (J·s)
c = 299792458       # Speed of light (m/s)
K_m = 683           # Luminous efficacy of photopic vision (lm/W) at 555 nm

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data') if '__file__' in globals() else 'data'
_data_cache = {}

def _load_csv(filename):
    """Loads and caches CSV reference datasets from the package data directory."""
    if filename not in _data_cache:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            _data_cache[filename] = pd.read_csv(filepath)
        else:
            _data_cache[filename] = None
    return _data_cache[filename]

# ============================================================================
# CORE MATHEMATICAL FUNCTIONS
# ============================================================================

def photonenergy(wavelength):
    """Calculates photon energy (E = hc / λ) in Joules."""
    wavelength = np.asarray(wavelength, dtype=float)
    return (h * c) / (wavelength * 1e-9)

def govardovskii(lmax, wavelength):
    """
    Govardovskii et al. (2000) universal visual pigment template.
    Computes unfiltered photon sensitivity for a given lambda_max.
    """
    wavelength = np.asarray(wavelength, dtype=float)
    lmax = float(lmax)
    
    # Template parameters
    bband = 189 + 0.315 * lmax
    fmaxa = 3e17 / lmax
    fmaxb = 3e17 / bband
    Aa = 69.7
    Ab = 0.26
    a = 0.8795 + 0.0459 * np.exp(-((lmax - 300) ** 2) / 11940)
    B = 28
    b = 0.922
    C = -14.9
    c = 1.104
    D = 0.674
    d = -40.5 + 0.195 * lmax
    
    # Convert wavelengths to frequency
    freq = 3e17 / wavelength
    ffmax = freq / fmaxa
    
    # Alpha band (Sa) and Beta band (Sb)
    Sa = 1 / (np.exp(Aa * (a - ffmax)) + np.exp(B * (b - ffmax)) + np.exp(C * (c - ffmax)) + D)
    Sb = Ab * np.exp(-((wavelength - bband) / d) ** 2)
    
    aspecp = Sa + Sb
    return aspecp / np.max(aspecp)

def vlambda(power, wavelength):
    """
    Calculate photopic illuminance (lux) or luminance (cd/m²).
    Sorts, deduplicates, and interpolates inputs to 1 nm spacing.
    """
    power = np.asarray(power, dtype=float).flatten()
    wavelength = np.asarray(wavelength, dtype=float).flatten()
    
    if len(power) != len(wavelength):
        raise ValueError("power and wavelength arrays must have the same length.")
        
    # Clean input data: Sort and drop duplicate wavelengths
    df_temp = pd.DataFrame({'wavelength': wavelength, 'power': power})
    df_temp = df_temp.drop_duplicates(subset=['wavelength']).sort_values('wavelength')
    wavelength = df_temp['wavelength'].values
    power = df_temp['power'].values
    
    # Interpolate to 1nm steps if wavelength spacing is not 1nm
    wl_spacing = np.mean(np.diff(wavelength))
    if not np.isclose(wl_spacing, 1.0):
        wlo = wavelength
        wavelength = np.arange(np.round(wlo[0]), np.round(wlo[-1]) + 1, dtype=float)
        f_spline = interpolate.CubicSpline(wlo, power, bc_type='natural')
        power = f_spline(wavelength) / np.mean(np.diff(wlo))
        
    vlambda_df = _load_csv('VisualStandards_vlambda.csv')
    if vlambda_df is None or len(vlambda_df) == 0:
        return 0.0
        
    vlam_wl = vlambda_df['wavelen'].values
    vlam_values = vlambda_df['photopic'].values
    
    f_vlam = interpolate.interp1d(vlam_wl, vlam_values, kind='cubic', bounds_error=False, fill_value=0.0)
    vlam_interp = f_vlam(wavelength)
    
    return K_m * np.sum(power * vlam_interp)

def harmonisesens(sens, target_range):
    """Trims and pads a predefined sensitivity array to match target_range."""
    wls = np.asarray(sens['wavelen'], dtype=float)
    ph = np.asarray(sens['aspecp'], dtype=float)
    
    delta_short = int(wls[0] - target_range[0])
    if delta_short > 0:
        ph = np.concatenate([np.full(delta_short, np.nan), ph])
        wls = np.arange(target_range[0], wls[-1] + 1)
    elif delta_short < 0:
        ph = ph[-delta_short:]
        wls = wls[-delta_short:]
        
    delta_long = int(wls[-1] - target_range[-1])
    if delta_long < 0:
        ph = np.concatenate([ph, np.full(-delta_long, np.nan)])
        wls = np.arange(wls[0], target_range[-1] + 1)
    elif delta_long > 0:
        ph = ph[:len(ph) - delta_long]
        wls = wls[:len(wls) - delta_long]
        
    return ph

def harmonisetrans(pfilter, target_range):
    """Extrapolates and trims transmission data to match target_range."""
    wlp = np.asarray(pfilter['wavelen'], dtype=float)
    trans = np.asarray(pfilter['trans'], dtype=float)
    
    delta_short = int(wlp[0] - target_range[0])
    if delta_short > 0:
        avg_delta = np.mean(np.diff(trans[:3]))
        extra = trans[0] - avg_delta * np.arange(delta_short, 0, -1)
        extra[extra < 0] = 0.0
        trans = np.concatenate([extra, trans])
        wlp = np.arange(target_range[0], wlp[-1] + 1)
    elif delta_short < 0:
        trans = trans[-delta_short:]
        wlp = wlp[-delta_short:]
        
    delta_long = int(target_range[-1] - wlp[-1])
    if delta_long > 0:
        trans = np.concatenate([trans, np.full(delta_long, trans[-1])])
        wlp = np.arange(wlp[0], target_range[-1] + 1)
    elif delta_long < 0:
        trans = trans[:len(trans) + delta_long]
        wlp = wlp[:len(wlp) + delta_long]
        
    return np.clip(trans, 0.0, 100.0)

def generateaopicactionspec(opsin="Mel", lmax=None, pfilter=None, range_wl=None):
    """Generates the species-specific alpha-opic action spectrum."""
    if range_wl is None:
        range_wl = np.arange(300, 801, dtype=float)
    else:
        range_wl = np.asarray(range_wl, dtype=float)

    # Smart Defaulting for pfilter: Default to lmax if it's a species string
    if pfilter is None:
        pfilter = lmax if isinstance(lmax, str) else 0

    # ========== Get photon-based spectral sensitivity ==========
    # BIOLOGICAL PRINCIPLE: Only Human action spectra are pre-corrected for lens filtering
    # in the R package's VisualStandards. All non-human mammalian curves represent
    # photoreceptor-only sensitivities (in vitro) and must be filtered by the lens.
    lens_already_applied = False
    if isinstance(lmax, str) and lmax.lower() == 'human':
        lens_already_applied = True
    
    if isinstance(lmax, (int, float)) and lmax > 0:
        aspecp = govardovskii(lmax, range_wl)
    elif isinstance(lmax, str):
        sens_df = _load_csv(f'SensRefData_{opsin}.csv')
        if sens_df is not None and len(sens_df) > 0:
            # Filter to species and remove NaN rows
            species_data = sens_df[
                (sens_df['species'].str.lower() == lmax.lower()) & 
                (sens_df['aspecp'].notna())
            ]
            if len(species_data) > 0:
                sens_dict = {
                    'wavelen': species_data['wavelen'].values,
                    'aspecp': species_data['aspecp'].values
                }
                aspecp = harmonisesens(sens_dict, range_wl)
            else:
                raise ValueError(
                    f"Opsin '{opsin}' is not measured/available for species '{lmax}' in the database."
                )
        else:
            raise ValueError(f"Database file for Opsin '{opsin}' could not be located.")
    else:
        # Default behavior for pure numeric modeling
        aspecp = govardovskii(480, range_wl)

    # ========== Get prereceptoral transmission ==========
    if isinstance(pfilter, (int, float)) and len(np.atleast_1d(pfilter)) == 1:
        trans = np.ones(len(range_wl)) * 100.0
    elif isinstance(pfilter, str):
        trans_df = _load_csv('TransRefData.csv')
        if trans_df is not None and len(trans_df) > 0:
            species_trans = trans_df[trans_df['species'].str.lower() == pfilter.lower()]
            if len(species_trans) > 0:
                trans_dict = {
                    'wavelen': species_trans['wavelen'].values,
                    'trans': species_trans['trans'].values
                }
                trans = harmonisetrans(trans_dict, range_wl)
            else:
                trans = np.ones(len(range_wl)) * 100.0
        else:
            trans = np.ones(len(range_wl)) * 100.0
    elif isinstance(pfilter, pd.DataFrame):
        trans_dict = {
            'wavelen': pfilter.iloc[:, 0].values,
            'trans': pfilter.iloc[:, 1].values
        }
        trans = harmonisetrans(trans_dict, range_wl)
    else:
        trans = np.ones(len(range_wl)) * 100.0

    # ========== Apply lens correction filter ==========
    if lens_already_applied:
        aspecp_filtered = aspecp
    else:
        aspecp_filtered = aspecp * (trans / 100.0)

    # ========== Convert to energy spectrum & Normalize ==========
    e = photonenergy(range_wl)
    aspec = aspecp_filtered / e

    max_aspec = np.nanmax(aspec) if not np.all(np.isnan(aspec)) else 1.0
    max_aspecp = np.nanmax(aspecp_filtered) if not np.all(np.isnan(aspecp_filtered)) else 1.0
    
    if max_aspec > 0:
        aspec = aspec / max_aspec
    if max_aspecp > 0:
        aspecp_filtered = aspecp_filtered / max_aspecp

    aspec = np.nan_to_num(aspec, nan=0.0)
    aspecp_filtered = np.nan_to_num(aspecp_filtered, nan=0.0)

    # ========== Calculate kavD65 using spline interpolation ==========
    d65_data = _load_csv('VisualStandards_D65.csv')
    if d65_data is not None and len(d65_data) > 0:
        d65_wl = d65_data['wavelen'].values
        d65_spectra = d65_data['spectra'].values
        d65_lux = d65_data['lux'].iloc[0]
        
        f_d65 = interpolate.interp1d(d65_wl, d65_spectra, kind='cubic', bounds_error=False, fill_value=0.0)
        d65_sp = f_d65(range_wl)
        
        kavD65 = np.sum(d65_sp * aspec) / d65_lux
    else:
        kavD65 = 1.0

    if kavD65 <= 0:
        kavD65 = 1.0

    return {
        'opsin': opsin,
        'wavelen': range_wl,
        'trans': trans,
        'aspecp': aspecp_filtered,
        'aspec': aspec,
        'kavD65': kavD65
    }

def alphaopic(power, wavelength, opsin="Mel", lmax=None, pfilter=None):
    """
    Main alpha-opic calculator. EXACT mathematical translation of R's alphaopic().
    Returns a pandas DataFrame matching R's return structure.
    """
    power = np.asarray(power, dtype=float).flatten()
    wavelength = np.asarray(wavelength, dtype=float).flatten()

    if len(power) != len(wavelength):
        raise ValueError("power and wavelength must have same length")

    # Clean input data: Sort and drop duplicate wavelengths
    df_temp = pd.DataFrame({'wavelength': wavelength, 'power': power})
    df_temp = df_temp.drop_duplicates(subset=['wavelength']).sort_values('wavelength')
    wavelength = df_temp['wavelength'].values
    power = df_temp['power'].values

    # Spline interpolation to 1 nm spacing if required
    wl = wavelength.copy()
    wl_spacing = np.mean(np.diff(wl))
    if not np.isclose(wl_spacing, 1.0):
        wlo = wl
        wl = np.arange(np.round(wlo[0]), np.round(wlo[-1]) + 1, dtype=float)
        f_spline = interpolate.CubicSpline(wlo, power, bc_type='natural')
        power = f_spline(wl) / np.mean(np.diff(wlo))

    # Calculate action spectrum (will raise ValueError if opsin is missing for species)
    aopics = generateaopicactionspec(opsin, lmax, pfilter, wl)
    crv = aopics['aspec']
    crvp = aopics['aspecp']
    const = aopics['kavD65']
    wavelen = aopics['wavelen']

    e = photonenergy(wavelen)

    # Calculate metrics
    Luminous = np.sum(power * crv) / const
    Radiant = np.sum(power * crv)
    
    with np.errstate(divide='ignore'):
        Photon = np.log10(np.sum(power * crvp / (e * 10000)))

    # Returns DataFrame matching R's data.frame outputs
    return pd.DataFrame({
        'Luminous': [float(Luminous)],
        'Radiant': [float(Radiant)],
        'Photon': [float(Photon)]
    })

def aopicspecies():
    """Returns a taxonomy table for all 64 species in the reference database."""
    species_data = _load_csv('SpeciesListData.csv')
    if species_data is not None and len(species_data) > 0:
        if 'Unnamed: 0' in species_data.columns:
            species_data = species_data.drop(columns=['Unnamed: 0'])
        return species_data.reset_index(drop=True)
    return pd.DataFrame()

# ============================================================================
# NAMESPACE REGISTRATION (Supports "from alphaopics_main import alphaopics")
# ============================================================================
alphaopics = sys.modules[__name__]
sys.modules['alphaopics_main.alphaopics'] = sys.modules[__name__]
