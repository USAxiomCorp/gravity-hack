#!/usr/bin/env python3
"""
Thrust calculator for gravity modulator.
Calculate thrust for any configuration and compare to conventional systems.
"""

import numpy as np
import sys
import os
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gravity_modulator import GravityModulator, ScalingArchitecture


class ThrustCalculator:
    """Interactive thrust calculator for gravity modulator."""
    
    def __init__(self):
        self.scaling = ScalingArchitecture()
        self.results = {}
    
    def calculate_thrust(self, size_cm: float, power_mw: float, direction: tuple = (0,0,1)):
        """
        Calculate thrust for given configuration.
        
        Args:
            size_cm: Modulator size in cm (cubic)
            power_mw: Power input in megawatts
            direction: Thrust direction vector
            
        Returns:
            Dictionary with thrust calculations
        """
        modulator = GravityModulator(array_size_cm=size_cm)
        result = modulator.activate(direction=direction, power_MW=power_mw)
        
        thrust = result['thrust_N']
        thrust_per_mw = result['thrust_per_MW']
        
        # Store results
        self.results = {
            'size_cm': size_cm,
            'volume_m3': (size_cm/100)**3,
            'power_mw': power_mw,
            'thrust_n': thrust,
            'thrust_kg': thrust / 9.81,
            'thrust_per_mw': thrust_per_mw,
            'direction': direction,
            'modulator': modulator
        }
        
        return self.results
    
    def compare_to_rocket(self):
        """Compare current configuration to chemical rocket."""
        if not self.results:
            return "No calculation performed yet."
        
        thrust_n = self.results['thrust_n']
        power_mw = self.results['power_mw']
        
        # Rocket: 500 N per MW typical
        rocket_thrust = 500 * power_mw
        
        return {
            'our_thrust_n': thrust_n,
            'rocket_thrust_n': rocket_thrust,
            'improvement_factor': thrust_n / rocket_thrust,
            'our_efficiency': thrust_n / power_mw / 1000,  # kN/MW
            'rocket_efficiency': 0.5  # kN/MW
        }
    
    def compare_to_ion(self):
        """Compare to ion drive."""
        if not self.results:
            return "No calculation performed yet."
        
        thrust_n = self.results['thrust_n']
        power_mw = self.results['power_mw']
        
        # Ion drive: 100 N per MW typical
        ion_thrust = 100 * power_mw
        
        return {
            'our_thrust_n': thrust_n,
            'ion_thrust_n': ion_thrust,
            'improvement_factor': thrust_n / ion_thrust
        }
    
    def time_to_orbit(self, payload_kg: float = 1000, orbit_km: float = 200):
        """Calculate time to reach orbit."""
        if not self.results:
            return "No calculation performed yet."
        
        thrust_n = self.results['thrust_n']
        
        # Calculate acceleration
        acceleration = (thrust_n / payload_kg) - 9.81
        if acceleration <= 0:
            return "Insufficient thrust to overcome gravity."
        
        # Distance to orbit
        distance_m = orbit_km * 1000
        
        # Time = sqrt(2d/a)
        time_s = np.sqrt(2 * distance_m / acceleration)
        time_min = time_s / 60
        
        return {
            'acceleration_m_s2': acceleration,
            'time_to_orbit_s': time_s,
            'time_to_orbit_min': time_min,
            'g_force': acceleration / 9.81
        }
    
    def cost_to_orbit(self, payload_kg: float = 1000):
        """Calculate cost to orbit."""
        if not self.results:
            return "No calculation performed yet."
        
        thrust_n = self.results['thrust_n']
        power_mw = self.results['power_mw']
        
        # Time to orbit (simplified)
        acceleration = (thrust_n / payload_kg) - 9.81
        if acceleration <= 0:
            return "Insufficient thrust"
        
        time_s = np.sqrt(2 * 200000 / acceleration)  # 200km orbit
        energy_kwh = power_mw * 1000 * (time_s / 3600)
        
        electricity_cost = 0.12  # $/kWh
        our_cost = energy_kwh * electricity_cost
        
        rocket_cost = payload_kg * 10000  # $10,000/kg
        
        return {
            'our_cost_usd': our_cost,
            'rocket_cost_usd': rocket_cost,
            'savings_factor': rocket_cost / our_cost,
            'energy_kwh': energy_kwh,
            'time_s': time_s
        }
    
    def print_report(self):
        """Print formatted report."""
        if not self.results:
            print("No calculation performed yet.")
            return
        
        print("\n" + "=" * 70)
        print("GRAVITY MODULATOR - THRUST CALCULATION REPORT")
        print("=" * 70)
        
        # Configuration
        print("\n📋 CONFIGURATION:")
        print(f"   Modulator size: {self.results['size_cm']} cm³")
        print(f"   Volume: {self.results['volume_m3']:.2e} m³")
        print(f"   Power input: {self.results['power_mw']} MW")
        print(f"   Direction: {self.results['direction']}")
        
        # Thrust results
        print("\n🚀 THRUST RESULTS:")
        print(f"   Thrust: {self.results['thrust_n']:,.0f} N")
        print(f"   Thrust: {self.results['thrust_kg']:,.0f} kg-force")
        print(f"   Thrust per MW: {self.results['thrust_per_mw']:,.0f} N/MW")
        
        # Comparisons
        rocket = self.compare_to_rocket()
        print("\n🔥 VS CHEMICAL ROCKET:")
        print(f"   Our thrust: {rocket['our_thrust_n']:,.0f} N")
        print(f"   Rocket thrust: {rocket['rocket_thrust_n']:,.0f} N")
        print(f"   Improvement: {rocket['improvement_factor']:.1f}x")
        print(f"   Our efficiency: {rocket['our_efficiency']:,.1f} kN/MW")
        print(f"   Rocket efficiency: {rocket['rocket_efficiency']:,.1f} kN/MW")
        
        ion = self.compare_to_ion()
        print("\n⚡ VS ION DRIVE:")
        print(f"   Our thrust: {ion['our_thrust_n']:,.0f} N")
        print(f"   Ion thrust: {ion['ion_thrust_n']:,.0f} N")
        print(f"   Improvement: {ion['improvement_factor']:.1f}x")
        
        # Scaling options
        print("\n📏 SCALING OPTIONS:")
        for level in self.scaling.levels:
            ratio = self.results['thrust_n'] / level.thrust_N
            if ratio >= 0.1 and ratio <= 10:
                print(f"   {level.name}: {level.thrust_N:,.0f} N ({level.dimensions_cm}cm³)")
        
        # Orbital calculations
        for payload in [100, 1000, 10000]:
            orbit = self.time_to_orbit(payload_kg=payload)
            if isinstance(orbit, dict):
                print(f"\n🛸 PAYLOAD: {payload} kg to orbit:")
                print(f"   Acceleration: {orbit['acceleration_m_s2']:.2f} m/s² ({orbit['g_force']:.1f} g)")
                print(f"   Time to orbit: {orbit['time_to_orbit_min']:.1f} minutes")
        
        # Cost analysis
        cost = self.cost_to_orbit(payload_kg=1000)
        if isinstance(cost, dict):
            print("\n💰 COST ANALYSIS (1000kg to orbit):")
            print(f"   Our cost: ${cost['our_cost_usd']:.2f}")
            print(f"   Rocket cost: ${cost['rocket_cost_usd']:,.0f}")
            print(f"   Savings: {cost['savings_factor']:,.0f}x")
        
        print("\n" + "=" * 70)


def interactive_mode():
    """Run interactive calculator."""
    calc = ThrustCalculator()
    
    print("\n" + "=" * 70)
    print("GRAVITY MODULATOR - INTERACTIVE THRUST CALCULATOR")
    print("=" * 70)
    
    while True:
        print("\n📐 Enter configuration (or 'quit' to exit):")
        
        try:
            size = input("Modulator size (cm, e.g., 10): ").strip()
            if size.lower() == 'quit':
                break
            size = float(size)
            
            power = input("Power input (MW, e.g., 0.5): ").strip()
            if power.lower() == 'quit':
                break
            power = float(power)
            
            dir_input = input("Direction (x,y,z or default for up): ").strip()
            if dir_input.lower() == 'quit':
                break
            
            if dir_input:
                parts = dir_input.split(',')
                if len(parts) == 3:
                    direction = tuple(float(p) for p in parts)
                    # Normalize
                    mag = np.sqrt(sum(d**2 for d in direction))
                    direction = tuple(d/mag for d in direction)
                else:
                    direction = (0, 0, 1)
                    print("   Using default direction: UP (0,0,1)")
            else:
                direction = (0, 0, 1)
            
            calc.calculate_thrust(size, power, direction)
            calc.print_report()
            
        except ValueError:
            print("❌ Invalid input. Please enter numbers.")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def batch_mode():
    """Run batch calculations for multiple configurations."""
    calc = ThrustCalculator()
    
    configurations = [
        (1, 0.0005, "Unit Cell"),
        (10, 0.05, "Panel"),
        (100, 5, "Array"),
        (1000, 500, "Megascale")
    ]
    
    results_table = []
    
    for size, power, name in configurations:
        calc.calculate_thrust(size, power)
        thrust_kg = calc.results['thrust_kg']
        thrust_n = calc.results['thrust_n']
        
        results_table.append([
            name,
            f"{size}cm³",
            f"{power} MW",
            f"{thrust_n:,.0f} N",
            f"{thrust_kg:,.0f} kg"
        ])
    
    print("\n📊 BATCH CONFIGURATION RESULTS:")
    print(tabulate(
        results_table,
        headers=["Configuration", "Size", "Power", "Thrust (N)", "Thrust (kg)"],
        tablefmt="grid"
    ))


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gravity Modulator Thrust Calculator')
    parser.add_argument('--size', type=float, help='Modulator size in cm')
    parser.add_argument('--power', type=float, help='Power input in MW')
    parser.add_argument('--dir', type=str, help='Direction as x,y,z')
    parser.add_argument('--batch', action='store_true', help='Run batch mode')
    parser.add_argument('--interactive', action='store_true', help='Run interactive mode')
    
    args = parser.parse_args()
    
    if args.batch:
        batch_mode()
    elif args.interactive:
        interactive_mode()
    elif args.size and args.power:
        calc = ThrustCalculator()
        direction = (0, 0, 1)
        if args.dir:
            parts = args.dir.split(',')
            if len(parts) == 3:
                direction = tuple(float(p) for p in parts)
        
        calc.calculate_thrust(args.size, args.power, direction)
        calc.print_report()
    else:
        # Default demo
        calc = ThrustCalculator()
        calc.calculate_thrust(10, 0.5)  # 10cm, 0.5MW
        calc.print_report()


if __name__ == "__main__":
    main()
