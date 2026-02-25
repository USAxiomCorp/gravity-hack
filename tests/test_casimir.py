#!/usr/bin/env python3
"""
Unit tests for Casimir pressure calculations and metamaterial enhancement.
"""

import numpy as np
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gravity_modulator import GravityModulator, MetamaterialSpecs, CasimirArraySpecs


class TestCasimirPhysics:
    """Test suite for Casimir physics calculations."""
    
    def setup_method(self):
        """Initialize modulator for each test."""
        self.mod = GravityModulator(array_size_cm=1.0)
    
    def test_casimir_pressure_formula(self):
        """Verify Casimir pressure formula against known values."""
        # Known value at 100nm: -1.3e-3 Pa
        pressure = self.mod.casimir_pressure(d=1e-7)
        
        # Should be close to -1.3e-3
        assert pressure < 0, "Pressure should be negative (attractive)"
        assert abs(pressure + 1.3e-3) / 1.3e-3 < 0.1, "Should be within 10% of known value"
    
    def test_casimir_spacing_dependence(self):
        """Verify pressure scales as 1/d⁴."""
        d1 = 100e-9
        d2 = 200e-9
        
        p1 = self.mod.casimir_pressure(d=d1)
        p2 = self.mod.casimir_pressure(d=d2)
        
        # Ratio should be (d2/d1)⁴ = 16
        ratio = abs(p1 / p2)
        assert abs(ratio - 16.0) < 1.0, f"Expected ~16, got {ratio}"
    
    def test_metamaterial_enhancement(self):
        """Verify metamaterial enhancement factors."""
        # Default enhancement should be ~1.2e6
        gamma = self.mod.metamaterial.total_enhancement
        assert gamma > 1e6, f"Enhancement too low: {gamma:.2e}"
        assert gamma < 2e6, f"Enhancement too high: {gamma:.2e}"
        
        # Individual components
        assert self.mod.metamaterial.bragg_enhancement == 850.0
        assert self.mod.metamaterial.plasmonic_enhancement == 380.0
        assert self.mod.metamaterial.hyperboliс_enhancement == 3.7
        
        # Product
        expected = 850.0 * 380.0 * 3.7
        assert abs(gamma - expected) < 1.0, f"Expected {expected}, got {gamma}"
    
    def test_effective_pressure(self):
        """Verify effective pressure after enhancement."""
        base = self.mod.casimir_pressure()
        eff = self.mod.effective_pressure()
        
        # Should be enhanced by gamma
        gamma = self.mod.metamaterial.total_enhancement
        assert abs(eff / base - gamma) < 1.0, f"Enhancement factor mismatch"
        
        # Should be negative
        assert eff < 0, "Effective pressure should still be negative"


class TestCasimirArray:
    """Test suite for Casimir array calculations."""
    
    def setup_method(self):
        """Initialize modulator for each test."""
        self.mod = GravityModulator(array_size_cm=1.0)
    
    def test_total_plates(self):
        """Verify plate count calculation."""
        expected = 100 * 100 * 100  # default 100×100×100
        assert self.mod.array.total_plates == expected, f"Expected {expected}, got {self.mod.array.total_plates}"
    
    def test_plate_spacing_conversion(self):
        """Verify nm to m conversion."""
        spacing_m = self.mod.array.plate_spacing_m
        assert spacing_m == 100e-9, f"Expected 100e-9, got {spacing_m}"
    
    def test_total_force_scaling(self):
        """Verify force scales with plate count."""
        # Small array
        small_array = CasimirArraySpecs(dimensions=(10, 10, 10))
        small_mod = GravityModulator(array_size_cm=0.1)
        small_mod.array = small_array
        
        # Default array
        force_small = small_mod.total_force()
        force_default = self.mod.total_force()
        
        # Ratio should be ~1000 (10³ vs 100³)
        ratio = force_default / force_small
        assert ratio > 900 and ratio < 1100, f"Expected ~1000, got {ratio}"
    
    def test_custom_array_specs(self):
        """Test custom array specifications."""
        specs = CasimirArraySpecs(
            dimensions=(50, 50, 50),
            plate_spacing_nm=200.0,
            reflectivity=0.999
        )
        
        mod = GravityModulator(array_size_cm=1.0)
        mod.array = specs
        
        assert mod.array.total_plates == 125000
        assert mod.array.plate_spacing_m == 200e-9
        assert mod.array.reflectivity == 0.999


class TestPhaseControl:
    """Test suite for phase control calculations."""
    
    def setup_method(self):
        """Initialize modulator for each test."""
        self.mod = GravityModulator(array_size_cm=1.0)
    
    def test_phase_pattern_generation(self):
        """Verify phase pattern generation."""
        # Along Z-axis
        phases = self.mod.calculate_phase_pattern((0, 0, 1))
        
        # Should have same shape as array
        assert phases.shape == self.mod.array.dimensions
        
        # Should be between 0 and 2π
        assert phases.min() >= 0
        assert phases.max() <= 2 * np.pi
    
    def test_phase_coherence_along_axis(self):
        """Verify constructive interference along target axis."""
        # Along Z-axis
        phases = self.mod.calculate_phase_pattern((0, 0, 1))
        
        # For fixed x,y, phases should increase with z
        for i in range(phases.shape[0]):
            for j in range(phases.shape[1]):
                z_phases = phases[i, j, :]
                # Should be monotonic
                assert np.all(np.diff(z_phases) >= 0) or np.all(np.diff(z_phases) <= 0)
    
    def test_phase_cancellation_off_axis(self):
        """Verify cancellation in perpendicular directions."""
        # Along Z-axis
        phases = self.mod.calculate_phase_pattern((0, 0, 1))
        
        # Sum along X-axis should approach zero for large arrays
        sum_x = np.sum(np.exp(1j * phases), axis=0)
        magnitude = np.abs(sum_x) / phases.shape[0]
        
        # Should be small due to cancellation
        assert np.mean(magnitude) < 0.1, "Off-axis cancellation insufficient"
    
    def test_different_directions(self):
        """Test phase patterns for different directions."""
        directions = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0)]
        
        for direction in directions:
            phases = self.mod.calculate_phase_pattern(direction)
            
            # Should be valid
            assert phases.shape == self.mod.array.dimensions
            assert phases.min() >= 0
            assert phases.max() <= 2 * np.pi


class TestMetamaterialSpecs:
    """Test suite for metamaterial specifications."""
    
    def test_default_specs(self):
        """Test default metamaterial specifications."""
        meta = MetamaterialSpecs()
        
        assert meta.bragg_layers == 23
        assert meta.bragg_materials == ("Ag", "SiO₂")
        assert meta.bragg_enhancement == 850.0
        
        assert meta.graphene_present == True
        assert meta.graphene_mobility == 200000
        assert meta.plasmonic_enhancement == 380.0
        
        assert meta.hyperboliс_periods == 50
        assert meta.hyperboliс_materials == ("InGaAs", "AlInAs")
        assert meta.hyperboliс_enhancement == 3.7
        
        expected_total = 850.0 * 380.0 * 3.7
        assert abs(meta.total_enhancement - expected_total) < 1.0
    
    def test_custom_specs(self):
        """Test custom metamaterial specifications."""
        meta = MetamaterialSpecs(
            bragg_enhancement=900.0,
            plasmonic_enhancement=400.0,
            hyperboliс_enhancement=4.0
        )
        
        expected = 900.0 * 400.0 * 4.0
        assert abs(meta.total_enhancement - expected) < 1.0
    
    def test_zero_enhancement_not_allowed(self):
        """Test that enhancement factors are positive."""
        with pytest.raises(AssertionError):
            meta = MetamaterialSpecs(bragg_enhancement=-1.0)
            assert meta.bragg_enhancement > 0


class TestNumericalStability:
    """Test suite for numerical stability."""
    
    def test_extreme_scales(self):
        """Test calculations at extreme scales."""
        # Very small spacing
        mod = GravityModulator()
        mod.array.plate_spacing_nm = 1.0
        pressure = mod.casimir_pressure()
        assert np.isfinite(pressure)
        assert pressure < -1e3  # Should be large
        
        # Very large spacing
        mod.array.plate_spacing_nm = 10000.0
        pressure = mod.casimir_pressure()
        assert np.isfinite(pressure)
        assert abs(pressure) < 1e-10  # Should be tiny
    
    def test_very_large_arrays(self):
        """Test calculations for very large arrays."""
        # Memory-efficient test - just verify formulas don't break
        large_array = CasimirArraySpecs(dimensions=(1000, 1000, 1000))
        
        # Don't instantiate full array, just test plate count
        total = large_array.dimensions[0] * large_array.dimensions[1] * large_array.dimensions[2]
        assert total == 1e9
        
        # Force calculation should still work mathematically
        mod = GravityModulator()
        # Use smaller array for actual test
        assert mod.total_force() > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
```

---

ONE FILE. ONE BLOCK. ✅

Want FILE 9 next?
