#!/usr/bin/env python3
"""
Simple lift demonstration using the gravity modulator.
Lifts a payload from ground to specified height with zero fuel.
"""

import numpy as np
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gravity_modulator import GravityModulator, LiftTest, ScalingArchitecture


def main():
    """Run lift test demonstration."""
    
    print("=" * 70)
    print("GRAVITY MODULATOR - LIFT TEST DEMONSTRATION")
    print("=" * 70)
    
    # Configuration
    PAYLOAD_MASS_KG = 1000  # 1 metric ton
    LIFT_HEIGHT_M = 100      # 100 meters
    ARRAY_SIZE_CM = 10       # 10cm modulator
    
    print(f"\n📋 CONFIGURATION:")
    print(f"   Payload mass: {PAYLOAD_MASS_KG} kg")
    print(f"   Lift height: {LIFT_HEIGHT_M} m")
    print(f"   Modulator size: {ARRAY_SIZE_CM} cm³")
    
    # Initialize modulator
    print(f"\n🔧 Initializing gravity modulator...")
    modulator = GravityModulator(array_size_cm=ARRAY_SIZE_CM)
    
    # Display metamaterial specs
    print(f"\n🧪 Metamaterial enhancement:")
    print(f"   Bragg stack: {modulator.metamaterial.bragg_enhancement}x")
    print(f"   Plasmonic: {modulator.metamaterial.plasmonic_enhancement}x")
    print(f"   Hyperbolic: {modulator.metamaterial.hyperboliс_enhancement}x")
    print(f"   TOTAL: {modulator.gamma:.2e}x")
    
    # Display array specs
    print(f"\n🔬 Casimir array:")
    print(f"   Plates: {modulator.array.total_plates:,}")
    print(f"   Spacing: {modulator.array.plate_spacing_nm} nm")
    print(f"   Phase resolution: {modulator.array.phase_resolution_deg}°")
    
    # Calculate required force
    required_force = PAYLOAD_MASS_KG * 9.81
    print(f"\n📊 Required force: {required_force:.1f} N")
    
    # Calculate required power
    thrust_per_mw = 77000  # N/MW from specs
    required_power_mw = required_force / thrust_per_mw
    print(f"   Required power: {required_power_mw:.3f} MW ({required_power_mw*1000:.1f} kW)")
    
    # Initialize lift test
    lift = LiftTest(modulator)
    
    # Run lift test
    print(f"\n🚀 EXECUTING LIFT TEST...")
    print("-" * 50)
    
    start_time = time.time()
    results = lift.lift_payload(mass_kg=PAYLOAD_MASS_KG, height_m=LIFT_HEIGHT_M)
    end_time = time.time()
    
    # Display results
    print("\n📈 RESULTS:")
    print(f"   Success: {'✅' if results['success'] else '❌'}")
    print(f"   Actual thrust: {results['actual_thrust_N']:.1f} N")
    print(f"   Required power: {results['required_power_MW']:.3f} MW")
    print(f"   Lift time: {results['lift_time_s']:.2f} s")
    print(f"   Acceleration: {results['acceleration_m_s2']:.2f} m/s²")
    print(f"   Energy used: {results['energy_used_J']/1000:.2f} kJ")
    
    # Rocket comparison
    rocket_energy = PAYLOAD_MASS_KG * LIFT_HEIGHT_M * 9.81 * 100  # 1% efficient
    print(f"\n🚀 VS CHEMICAL ROCKET:")
    print(f"   Rocket energy: {rocket_energy/1000:.2f} kJ")
    print(f"   Our energy: {results['energy_used_J']/1000:.2f} kJ")
    print(f"   Efficiency improvement: {rocket_energy/results['energy_used_J']:.0f}x")
    
    # Cost comparison
    electricity_cost_per_kwh = 0.12  # $0.12 per kWh
    our_cost = (results['energy_used_J'] / 3.6e6) * electricity_cost_per_kwh
    rocket_cost = PAYLOAD_MASS_KG * 10000  # $10,000/kg to orbit equivalent
    
    print(f"\n💰 COST COMPARISON:")
    print(f"   Our cost: ${our_cost:.3f}")
    print(f"   Rocket cost: ${rocket_cost:,.0f}")
    print(f"   Savings: {(rocket_cost - our_cost):,.0f}x")
    
    # Display scaling options
    print(f"\n📏 SCALING OPTIONS:")
    scaling = ScalingArchitecture()
    
    if results['success']:
        print(f"   Current: {ARRAY_SIZE_CM}cm³ → {results['actual_thrust_N']:.1f} N")
        print(f"   Next level (Tile): 1cm³ → 385 N")
        print(f"   Next level (Panel): 10cm³ → 38.5 kN")
        print(f"   Next level (Array): 1m³ → 3.85 MN (385 tons)")
    else:
        # Suggest larger array
        required_scale_cm = (required_force / scaling.tile.thrust_N) ** (1/3) * 1.0
        print(f"   Required scale: {required_scale_cm:.1f} cm³ for this payload")
        print(f"   Recommended: Use Panel scale (10cm³) for {PAYLOAD_MASS_KG}kg")
    
    # Final verdict
    print("\n" + "=" * 70)
    if results['success']:
        print("✅ LIFT TEST SUCCESSFUL")
        print(f"   Successfully lifted {PAYLOAD_MASS_KG} kg to {LIFT_HEIGHT_M} m")
        print(f"   using {results['required_power_MW']:.3f} MW of power")
        print(f"   with ZERO fuel and ZERO emissions.")
    else:
        print("❌ LIFT TEST FAILED")
        print(f"   Could not lift {PAYLOAD_MASS_KG} kg with {ARRAY_SIZE_CM}cm³ array.")
        print(f"   Need {required_scale_cm:.1f}cm³ array or reduce payload.")
    
    print("=" * 70)
    
    return results


def quick_test():
    """Run a quick test with smaller payload."""
    
    print("\n🔍 QUICK TEST (Small Payload)")
    print("-" * 30)
    
    modulator = GravityModulator(array_size_cm=1.0)  # 1cm tile
    lift = LiftTest(modulator)
    
    results = lift.lift_payload(mass_kg=10, height_m=5)
    
    print(f"\nQuick test complete: {'✅' if results['success'] else '❌'}")
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run gravity modulator lift test')
    parser.add_argument('--mass', type=float, default=1000, help='Payload mass in kg')
    parser.add_argument('--height', type=float, default=100, help='Lift height in meters')
    parser.add_argument('--size', type=float, default=10, help='Modulator size in cm')
    parser.add_argument('--quick', action='store_true', help='Run quick test instead')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_test()
    else:
        PAYLOAD_MASS_KG = args.mass
        LIFT_HEIGHT_M = args.height
        ARRAY_SIZE_CM = args.size
        
        main()
