import numpy as np
import matplotlib.pyplot as plt

def calculate_uncertainty_distance(epsilon_z, z1, z2, x1_px, y1_px, x2_px, y2_px, hfov, h_pixels):
    # Calculate cm per pixel for each depth value
    cm_per_px_1 = (2 * z1 * np.tan(np.radians(hfov / 2))) / h_pixels
    cm_per_px_2 = (2 * z2 * np.tan(np.radians(hfov / 2))) / h_pixels

    # Calculate the x and y coordinates in cm
    x1_cm = x1_px * cm_per_px_1
    y1_cm = y1_px * cm_per_px_1
    x2_cm = x2_px * cm_per_px_2
    y2_cm = y2_px * cm_per_px_2

    # Calculate the Euclidean distance
    d = np.sqrt((x2_cm - x1_cm) ** 2 + (y2_cm - y1_cm) ** 2 + (z2 - z1) ** 2)

    # Calculate uncertainties in cm per pixel
    epsilon_cm_per_px_1 = (2 * np.tan(np.radians(hfov / 2)) / h_pixels) * epsilon_z
    epsilon_cm_per_px_2 = (2 * np.tan(np.radians(hfov / 2)) / h_pixels) * epsilon_z

    # Propagate errors to x and y coordinates
    epsilon_x1 = x1_px * epsilon_cm_per_px_1
    epsilon_y1 = y1_px * epsilon_cm_per_px_1
    epsilon_x2 = x2_px * epsilon_cm_per_px_2
    epsilon_y2 = y2_px * epsilon_cm_per_px_2

    # Calculate uncertainty in distance
    epsilon_dist = np.sqrt(
        (epsilon_x1 * (x2_cm - x1_cm) / d) ** 2 +
        (epsilon_y1 * (y2_cm - y1_cm) / d) ** 2 +
        (epsilon_z * (z2 - z1) / d) ** 2 +
        (epsilon_x2 * (x2_cm - x1_cm) / d) ** 2 +
        (epsilon_y2 * (y2_cm - y1_cm) / d) ** 2 +
        (epsilon_z * (z2 - z1) / d) ** 2
    )

    return epsilon_dist

# Parameters
z1 = 2000  # in cm
z2 = 3000  # in cm
x1_px, y1_px = 200, 300  # in pixels
x2_px, y2_px = 400, 500  # in pixels
hfov = 71.9  # Horizontal Field of View in degrees
h_pixels = 1280  # Horizontal resolution in pixels

epsilon_z_values = np.linspace(0, 0.5, 1000)
epsilon_dist_values = []

# calculate uncertainty in distance for 2% depth error in % 
print("Uncertainty in distance for 2% depth error: ", calculate_uncertainty_distance(0.02, z1, z2, x1_px, y1_px, x2_px, y2_px, hfov, h_pixels) * 100, "cm")

for epsilon_z in epsilon_z_values:
    epsilon_dist = calculate_uncertainty_distance(epsilon_z, z1, z2, x1_px, y1_px, x2_px, y2_px, hfov, h_pixels)
    epsilon_dist_values.append(epsilon_dist * 100)

# Plot the relationship
plt.figure(figsize=(10, 6))
plt.plot(epsilon_z_values * 100, epsilon_dist_values, label='Uncertainty in Distance', color='blue')
plt.xlabel('Depth Error Rate (\u03B5_z) %')
plt.ylabel('Distance Uncertainty (\u03B5_dist) cm')
plt.title('Relationship Between Depth Error Rate and Distance Uncertainty')
plt.grid(True)
plt.legend()
plt.show()
