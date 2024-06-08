import numpy as np
import xarray as xr

# start: a
# kai_tak: b1
# sung_wong_tai: b2

margin_meters = 20
voxel_edge_length_meters = 5
zero_ratio = 0.25

# meters
a_x_meters = 838825
a_y_meters = 819800
# tunnel_start_z_meters = 0

b1_x_meters = 838545
b1_y_meters = 821225
# tunnel_end_kai_tak_z_meters = 0 # -20

b2_x_meters = 837775
b2_y_meters = 820755
# tunnel_end_sung_wong_tai_z_meters = 0 # -20

voxel_grid_smallest_x_meters = min(a_x_meters, b1_x_meters, b2_x_meters) - margin_meters
voxel_grid_smallest_y_meters = min(a_y_meters, b1_y_meters, b2_y_meters) - margin_meters
# voxel_grid_smallest_z_meters = 0 # -50

voxel_grid_largest_x_meters = max(a_x_meters, b1_x_meters, b2_x_meters) + margin_meters
voxel_grid_largest_y_meters = max(a_y_meters, b1_y_meters, b2_y_meters) + margin_meters
# voxel_grid_largest_z_meters = 0

a_x_meters = 838825
a_y_meters = 819800
# tunnel_start_z_meters = 0

b1_x_meters = 838545
b1_y_meters = 821225
# tunnel_end_kai_tak_z_meters = 0 # -20

b2_x_meters = 837775
b2_y_meters = 820755
# tunnel_end_sung_wong_tai_z_meters = 0 # -20

# coordinates
a_x_voxel_coordinate = a_x_meters // voxel_edge_length_meters
a_y_voxel_coordinate = a_y_meters // voxel_edge_length_meters
# tunnel_start_z_voxel_coordinate = tunnel_start_z_meters // voxel_edge_length_meters

b1_x_voxel_coordinate = b1_x_meters // voxel_edge_length_meters
b1_y_voxel_coordinate = b1_y_meters // voxel_edge_length_meters
# tunnel_end_kai_tak_z_voxel_coordinate = tunnel_end_kai_tak_z_meters // voxel_edge_length_meters

b2_x_voxel_coordinate = b2_x_meters // voxel_edge_length_meters
b2_y_voxel_coordinate = b2_y_meters // voxel_edge_length_meters
# tunnel_end_sung_wong_tai_z_voxel_coordinate = tunnel_end_sung_wong_tai_z_meters // voxel_edge_length_meters

voxel_grid_smallest_x_voxel_coordinate = voxel_grid_smallest_x_meters // voxel_edge_length_meters
voxel_grid_smallest_y_voxel_coordinate = voxel_grid_smallest_y_meters // voxel_edge_length_meters
# voxel_grid_smallest_z_voxel_coordinate = voxel_grid_smallest_z_meters // voxel_edge_length_meters

voxel_grid_largest_x_voxel_coordinate = voxel_grid_largest_x_meters // voxel_edge_length_meters
voxel_grid_largest_y_voxel_coordinate = voxel_grid_largest_y_meters // voxel_edge_length_meters
# voxel_grid_largest_z_voxel_coordinate = voxel_grid_largest_z_meters // voxel_edge_length_meters

# generate values uniformly random between 0 and 1
data = np.random.uniform(low=0.0, high=1.0, size=(voxel_grid_largest_x_voxel_coordinate-voxel_grid_smallest_x_voxel_coordinate, voxel_grid_largest_y_voxel_coordinate-voxel_grid_smallest_y_voxel_coordinate))
random_zero_indices = np.random.choice(np.arange(data.size), replace=False,
                                       size=int(data.size * zero_ratio))
data[np.unravel_index(random_zero_indices, data.shape)] = 0

data = xr.DataArray(
    data=data,
    dims=("x", "y"),
    coords={
        "x": range(voxel_grid_smallest_x_voxel_coordinate, voxel_grid_largest_x_voxel_coordinate),
        "y": range(voxel_grid_smallest_y_voxel_coordinate, voxel_grid_largest_y_voxel_coordinate),
        # "z": range(voxel_grid_smallest_z_voxel_coordinate, voxel_grid_largest_z_voxel_coordinate),
    },
)

