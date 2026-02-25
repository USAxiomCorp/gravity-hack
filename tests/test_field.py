#!/usr/bin/env python3
"""
Unit tests for gravitational field equations and thrust calculations.
"""

import numpy as np
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gravity_modulator import GravityModulator, LiftTest, ScalingArchitecture


class TestGravitationalField:
    """Test suite for gravitational field calculations."""
    
    def setup_method(self):
        """Initialize modulator for each test."""
        self.mod = GravityModulator(array_size_cm=10.0)
    
    def test_stress_energy_tensor(self):
        """Verify stress-energy tensor properties."""
        # For Casimir effect: T_μν = diag(ρ, p, p, p) with ρ = -p
        pressure = abs(self.mod.effective_pressure())
        energy_density = pressure / (299792458 ** 2)  # ρ = p/c²
        
        # Weak energy condition violation: ρ + p < 0
        rho_plus_p = energy_density + pressure
        assert rho_plus_p < 0, "Weak energy condition should be violated"
        
        # For Casimir: ρ = -p/c², so ρ + p = p(1 - 1/c²) ≈ p (negative)
        assert rho_plus_p < 0, "Should have negative energy condition"
    
    def test_gravitational_potential_scaling(self):
        """Verify gravitational potential scales correctly."""
        # Potential Φ ∝ ∫ ρ/|r-r'| d³r'
        # For uniform density, Φ ∝ volume^(2/3)
        
        sizes = [1.0, 2.0, 5.0, 10.0]
        potentials = []
        
        for size in sizes:
            mod = GravityModulator(array_size_cm=size)
            # Approximate potential at surface
            volume = (size / 100) ** 3
            density = abs(mod.effective_pressure()) / (299792458 ** 2)
            # Φ ≈ G * density * volume^(2/3)
            potential = 6.67430e-11 * density * (volume ** (2/3))
            potentials.append(potential)
        
        # Check scaling: Φ₂/Φ₁ ≈ (V₂/V₁)^(2/3)
        ratio_10_1 = potentials[3] / potentials[0]
        volume_ratio = (10.0/1.0) ** 3
        expected_ratio = volume_ratio ** (2/3)  # (1000)^(2/3) = 100
        assert abs(ratio_10_1 / expected_ratio - 1.0) < 0.1, f"Expected {expected_ratio}, got {ratio_10_1}"
    
    def test_thrust_to_power_ratio(self):
        """Verify thrust per MW is constant."""
        self.mod.activate(power_MW=0.5)
        t1 = self.mod.thrust_per_MW()
        
        self.mod.activate(power_MW=1.0)
        t2 = self.mod.thrust_per_MW()
        
        # Should be the same
        assert abs(t1 - t2) / t1 < 0.01, f"Thrust/MW should be constant: {t1} vs {t2}"
        
        # Should be around 77,000 N/MW
        assert t1 > 70000 and t1 < 80000, f"Expected ~77000 N/MW, got {t1}"


class TestThrustCalculations:
    """Test suite for thrust calculations."""
    
    def setup_method(self):
        """Initialize modulator for each test."""
        self.mod = GravityModulator(array_size_cm=10.0)
    
    def test_thrust_directionality(self):
        """Verify thrust vector matches requested direction."""
        # Test different directions
        directions = [
            (1, 0, 0),
            (0, 1, 0), 
            (0, 0, 1),
            (1, 1, 0),
            (1, 1, 1)
        ]
        
        for direction in directions:
            # Normalize
            norm = np.sqrt(sum(d**2 for d in direction))
            dir_norm = tuple(d/norm for d in direction)
            
            result = self.mod.activate(direction=dir_norm, power_MW=0.5)
            
            # Thrust vector should align with direction
            thrust_dir = result['direction']
            dot_product = sum(a*b for a,b in zip(dir_norm, thrust_dir))
            
            assert dot_product > 0.99, f"Direction mismatch: {dir_norm} vs {thrust_dir}"
    
    def test_thrust_magnitude_vs_power(self):
        """Verify thrust scales linearly with power."""
        powers = [0.1, 0.2, 0.5, 1.0]
        thrusts = []
        
        for power in powers:
            result = self.mod.activate(power_MW=power)
            thrusts.append(result['thrust_N'])
        
        # Should be linear: T ∝ P
        ratios = [t/p for t, p in zip(thrusts, powers)]
        mean_ratio = np.mean(ratios)
        
        for ratio in ratios:
            assert abs(ratio - mean_ratio) / mean_ratio < 0.05, f"Non-linear scaling: {ratio} vs {mean_ratio}"
    
    def test_thrust_vs_array_size(self):
        """Verify thrust scales with array volume."""
        sizes = [1.0, 2.0, 5.0, 10.0]
        thrusts = []
        
        for size in sizes:
            mod = GravityModulator(array_size_cm=size)
            result = mod.activate(power_MW=0.5)
            thrusts.append(result['thrust_N'])
        
        # Should scale with volume (size³)
        ratios = [t / sizes[i]**3 for i, t in enumerate(thrusts)]
        mean_ratio = np.mean(ratios)
        
        for ratio in ratios:
            assert abs(ratio - mean_ratio) / mean_ratio < 0.1, f"Volume scaling error"
    
    def test_off_axis_cancellation(self):
        """Verify thrust in off-axis directions is minimal."""
        # Activate along Z
        result = self.mod.activate(direction=(0, 0, 1), power_MW=1.0)
        
        # Check X and Y components
        assert abs(result['direction'][0]) < 0.001, f"X-axis thrust too high: {result['direction'][0]}"
        assert abs(result['direction'][1]) < 0.001, f"Y-axis thrust too high: {result['direction'][1]}"


class TestLiftTest:
    """Test suite for lift demonstrations."""
    
    def setup_method(self):
        """Initialize modulator and lift test."""
        self.mod = GravityModulator(array_size_cm=10.0)
        self.lift = LiftTest(self.mod)
    
    def test_small_payload_lift(self):
        """Test lifting a small payload."""
        results = self.lift.lift_payload(mass_kg=100, height_m=10)
        
        assert results['success'] == True
        assert results['lift_time_s'] > 0
        assert results['energy_used_J'] > 0
    
    def test_heavy_payload_requires_more_power(self):
        """Test that heavier payloads require more power."""
        r1 = self.lift.lift_payload(mass_kg=100, height_m=10)
        r2 = self.lift.lift_payload(mass_kg=1000, height_m=10)
        
        # Power should scale with mass
        assert r2['required_power_MW'] > r1['required_power_MW']
        power_ratio = r2['required_power_MW'] / r1['required_power_MW']
        mass_ratio = 10.0
        assert abs(power_ratio - mass_ratio) / mass_ratio < 0.1
    
    def test_lift_height_affects_energy(self):
        """Test that higher lifts require more energy."""
        r1 = self.lift.lift_payload(mass_kg=100, height_m=10)
        r2 = self.lift.lift_payload(mass_kg=100, height_m=100)
        
        # Energy should scale with height
        energy_ratio = r2['energy_used_J'] / r1['energy_used_J']
        height_ratio = 10.0
        assert abs(energy_ratio - height_ratio) / height_ratio < 0.2
    
    def test_insufficient_power_fails(self):
        """Test that insufficient power results in failure."""
        # Use tiny modulator
        mod = GravityModulator(array_size_cm=0.1)
        lift = LiftTest(mod)
        
        results = lift.lift_payload(mass_kg=1000, height_m=10)
        assert results['success'] == False
    
    def test_rocket_comparison(self):
        """Test rocket efficiency comparison."""
        results = self.lift.lift_payload(mass_kg=100, height_m=10)
        
        # Calculate rocket energy (1% efficient)
        rocket_energy = results['mass_kg'] * results['height_m'] * 9.81 * 100
        
        improvement = rocket_energy / results['energy_used_J']
        assert improvement > 100, f"Expected >100x improvement, got {improvement:.0f}x"


class TestScalingArchitecture:
    """Test suite for scaling architecture."""
    
    def setup_method(self):
        """Initialize scaling architecture."""
        self.scaling = ScalingArchitecture()
    
    def test_scaling_levels(self):
        """Verify scaling levels are defined correctly."""
        assert len(self.scaling.levels) == 5
        
        # Unit cell
        assert self.scaling.unit_cell.name == "Unit Cell"
        assert self.scaling.unit_cell.thrust_N == 0.385
        
        # Tile
        assert self.scaling.tile.name == "Tile"
        assert self.scaling.tile.thrust_N == 385.0
        
        # Panel
        assert self.scaling.panel.name == "Panel"
        assert self.scaling.panel.thrust_N == 38500.0
        
        # Array
        assert self.scaling.array.name == "Array"
        assert self.scaling.array.thrust_N == 3850000.0
        
        # Megascale
        assert self.scaling.megascale.name == "Megascale"
        assert self.scaling.megascale.thrust_N == 38500000.0
    
    def test_scaling_ratios(self):
        """Verify thrust ratios between levels."""
        # Unit to Tile: 1000x (volume ratio)
        ratio_ut = self.scaling.tile.thrust_N / self.scaling.unit_cell.thrust_N
        assert abs(ratio_ut - 1000.0) < 10.0, f"Expected 1000x, got {ratio_ut:.0f}x"
        
        # Tile to Panel: 100x (10x dimension = 1000x volume, but panel uses 1000 tiles)
        ratio_tp = self.scaling.panel.thrust_N / self.scaling.tile.thrust_N
        assert abs(ratio_tp - 100.0) < 1.0, f"Expected 100x, got {ratio_tp:.0f}x"
        
        # Panel to Array: 100x
        ratio_pa = self.scaling.array.thrust_N / self.scaling.panel.thrust_N
        assert abs(ratio_pa - 100.0) < 1.0, f"Expected 100x, got {ratio_pa:.0f}x"
    
    def test_thrust_at_scale(self):
        """Test thrust calculation at arbitrary scale."""
        # 2cm should be 8x thrust of 1cm (2³ = 8)
        thrust_2cm = self.scaling.thrust_at_scale(2.0)
        thrust_1cm = self.scaling.tile.thrust_N
        assert abs(thrust_2cm / thrust_1cm - 8.0) < 0.1
        
        # 5cm should be 125x
        thrust_5cm = self.scaling.thrust_at_scale(5.0)
        assert abs(thrust_5cm / thrust_1cm - 125.0) < 1.0
    
    def test_display_method(self):
        """Test display method doesn't crash."""
        # Just verify it runs
        self.scaling.display_scaling()
        assert True


class TestEnergyCalculations:
    """Test suite for energy calculations."""
    
    def setup_method(self):
        """Initialize modulator."""
        self.mod = GravityModulator(array_size_cm=10.0)
    
    def test_power_to_thrust_efficiency(self):
        """Test power to thrust conversion efficiency."""
        self.mod.activate(power_MW=0.5)
        
        # Thrust per MW should be ~77,000 N/MW
        t_per_mw = self.mod.thrust_per_MW()
        assert t_per_mw > 75000 and t_per_mw < 78000
    
    def test_energy_vs_rocket(self):
        """Test energy comparison with rockets."""
        # Energy for 1000kg to 100m
        force = 1000 * 9.81
        work = force * 100  # Joules
        
        # Our energy (assuming 77,000 N/MW)
        power_mw = force / 77000
        time_s = np.sqrt(2 * 100 / (force/1000 - 9.81))
        energy_j = power_mw * 1e6 * time_s
        
        # Rocket energy (1% efficient)
        rocket_energy = work * 100
        
        assert rocket_energy / energy_j > 1000, "Should be >1000x more efficient"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
```

---

ONE FILE. ONE BLOCK. ✅

Want FILE 10 next?
