import pandas as pd
import os
import glob
import matplotlib.pyplot as plt

def read_data(file_path):
    return pd.read_csv(file_path, delim_whitespace=True, names=["Time", "Calculated_Distance", "Actual_Distance", "Error", "Mode"])

data_dir = 'logs/13.08.2024/'
txt_files = glob.glob(os.path.join(data_dir, "*.txt"))
all_data = pd.DataFrame()

for file in txt_files:
    if 'info.txt' not in file:  # Skip the info file
        # Extract the distance label from the file name (e.g., "100cm_100cm.txt" -> "100cm")
        distance_label = os.path.basename(file).split('_')[0]
        df = read_data(file)
        df['Distance_Level'] = distance_label
        all_data = pd.concat([all_data, df])

# Convert the distance label to a numeric value for further analysis
all_data['Distance_Level'] = all_data['Distance_Level'].str.replace('cm', '').astype(float) / 100  # Convert to meters

# Clean the Error, Calculated_Distance, and Actual_Distance columns
all_data['Error'] = pd.to_numeric(all_data['Error'], errors='coerce')
all_data['Calculated_Distance'] = pd.to_numeric(all_data['Calculated_Distance'], errors='coerce')
all_data['Actual_Distance'] = pd.to_numeric(all_data['Actual_Distance'], errors='coerce')

# Drop rows with NaN values in these columns
all_data = all_data.dropna(subset=['Error', 'Calculated_Distance', 'Actual_Distance'])

# Group by distance level and calculate error statistics
grouped_data = all_data.groupby('Distance_Level').agg(
    mean_error=('Error', 'mean'),
    std_dev_error=('Error', 'std'),
    mean_calculated_distance=('Calculated_Distance', 'mean'),
    mean_actual_distance=('Actual_Distance', 'mean')
)

# Calculate error rate
grouped_data['error_rate'] = grouped_data['mean_error'] / grouped_data['mean_actual_distance'] * 100

# Display the analysis results
print(grouped_data)

# Plot error rate vs distance
plt.figure(figsize=(10, 6))
plt.plot(grouped_data.index, grouped_data['error_rate'], marker='o')
plt.title('Error Rate vs Distance Level')
plt.xlabel('Distance Level (meters)')
plt.ylabel('Error Rate (%)')
plt.grid(True)
plt.show()
