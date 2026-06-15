class TrafficDensity:
    def calculate(self, active_vehicles):
        # Low traffic
        if active_vehicles <= 5:
            return "Low"

        # Medium traffic
        if active_vehicles <= 15:
            return "Medium"

        # High traffic
        return "High"


if __name__ == "__main__":
    density = TrafficDensity()
    print(density.calculate(3))
    print(density.calculate(10))
    print(density.calculate(20))