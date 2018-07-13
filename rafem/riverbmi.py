#! /usr/local/bin/python
"""Basic Model Interface implementation for River Module"""

import numpy as np
from six.moves import range

from .rivermodule import RiverModule


class BmiRiverModule(object):

    """The BMI for the River Avulsion Floodplain Evolution Model."""

    _name = "Rafem"
    _input_var_names = (
        "land_surface__elevation",
        "channel_exit__x_coordinate",
        "channel_exit__y_coordinate",
    )
    _output_var_names = (
        "channel_centerline__x_coordinate",
        "channel_centerline__y_coordinate",
        "channel_centerline__elevation",
        "channel_exit_water_sediment~bedload__volume_flow_rate",
        "channel_exit__x_coordinate",
        "channel_exit__y_coordinate",
        "land_surface__elevation",
        "sea_water_surface__elevation",
        # 'avulsion_record',
    )

    def __init__(self):
        """Create a BmiRiver module that is ready for initialization."""
        self._model = None
        self._values = {}
        self._var_units = {}

    def initialize(self, filename):
        """Initialize the River module."""
        self._model = RiverModule.from_path(filename)

        self._values = {
            "channel_centerline__x_coordinate": lambda: self._model.river_x_coordinates,
            "channel_centerline__y_coordinate": lambda: self._model.river_y_coordinates,
            "channel_exit_water_sediment~bedload__volume_flow_rate": lambda: np.array(
                self._model.sediment_flux
            ),
            "channel_exit__x_coordinate": lambda: np.array(
                self._model.river_x_coordinates[-1]
            ),
            "channel_exit__y_coordinate": lambda: np.array(
                self._model.river_y_coordinates[-1]
            ),
            "land_surface__elevation": lambda: np.array(self._model.elevation),
            "channel_centerline__elevation": lambda: self._model.profile,
            "sea_water_surface__elevation": lambda: np.array(self._model.sea_level),
            "avulsion_record": lambda: self._model.avulsions,
        }

        self._var_units = {
            "channel_centerline__x_coordinate": "m",
            "channel_centerline__y_coordinate": "m",
            "channel_exit_water_sediment~bedload__volume_flow_rate": "m^3 s^-1",
            "channel_exit__x_coordinate": "m",
            "channel_exit__y_coordinate": "m",
            "land_surface__elevation": "m",
            "channel_centerline__elevation": "m",
            "sea_water_surface__elevation": "m",
            "avulsion_record": "none",
        }

        self._var_type = {}
        for name in self._input_var_names + self._output_var_names:
            self._var_type[name] = str(np.dtype(float))

        self._var_grid = {
            "channel_centerline__x_coordinate": 1,
            "channel_centerline__y_coordinate": 1,
            "channel_exit_water_sediment~bedload__volume_flow_rate": 2,
            "channel_exit__x_coordinate": 2,
            "channel_exit__y_coordinate": 2,
            "land_surface__elevation": 0,
            "channel_centerline__elevation": 1,
            "sea_water_surface__elevation": 2,
            "avulsion_record": None,
        }

        self._grid_rank = {0: 2, 1: 1, 2: 0}

    def update(self):
        """Advance model by one time step."""
        self._model.advance_in_time()
        self.river_mouth_location = (
            self._model.river_x_coordinates[-1],
            self._model.river_y_coordinates[-1],
        )

    def update_frac(self, time_frac):
        """Update model by a fraction of a time step."""
        time_step = self.get_time_step()
        self._model.time_step = time_frac * time_step
        self.update()
        self._model.time_step = time_step

    def update_until(self, then):
        """Update model until a particular time."""
        n_steps = (then - self.get_current_time()) / self.get_time_step()

        for _ in range(int(n_steps)):
            self.update()
        # self.update_frac(n_steps - int(n_steps))

    def finalize(self):
        """Clean up & save avulsion file"""
        pass

    def get_var_type(self, var_name):
        """Data type of variable."""
        return self._var_type[var_name]
        # return str(self.get_value(var_name).dtype)

    def get_var_units(self, var_name):
        """Get units of variable."""
        return self._var_units[var_name]

    def get_var_nbytes(self, var_name):
        """Get units of variable."""
        return self.get_value(var_name).nbytes

    def get_var_itemsize(self, var_name):
        return np.dtype("float").itemsize

    def get_var_location(self, var_name):
        return "node"

    def get_var_grid(self, var_name):
        return self._var_grid[var_name]

    def get_grid_rank(self, grid_id):
        return self._grid_rank[grid_id]

    def get_grid_size(self, grid_id):
        if grid_id == 0:
            return int(np.prod(self._model.grid_shape))
        elif grid_id == 1:
            return len(self._model.river_x_coordinates)
        elif grid_id == 2:
            return 1
        else:
            raise KeyError(grid_id)

    def get_grid_shape(self, grid_id, out=None):
        if grid_id == 0:
            shape = self._model.grid_shape
        elif grid_id == 1:
            shape = self._model.river_x_coordinates.shape
        elif grid_id == 2:
            shape = (1,)
        else:
            raise KeyError(grid_id)

        if out is None:
            return shape
        else:
            out[:] = shape
            return out

    def get_grid_spacing(self, grid_id, out=None):
        if grid_id == 0:
            if out is None:
                return self._model.grid_spacing
            else:
                out[:] = self._model.grid_spacing
                return out

    def get_grid_origin(self, grid_id, out=None):
        if grid_id == 0:
            origin = (0., 0.)
            if out is None:
                return origin
            else:
                out[:] = origin
                return out

    def get_grid_type(self, grid_id):
        if grid_id == 0:
            return "uniform_rectilinear"
        elif grid_id == 1:
            return "vector"
        elif grid_id == 2:
            return "scalar"
        else:
            raise KeyError(grid_id)

    def get_value(self, var_name, out=None):
        """Copy of values."""
        if out is None:
            return self._values[var_name]()
        else:
            out[:] = self._values[var_name]().flat
            return out

    def set_value(self, var_name, new_vals):
        """Set model values."""
        if var_name not in self._input_var_names:
            raise KeyError(var_name)

        if var_name == "land_surface__elevation":
            np.copyto(self._model.elevation.reshape((-1,)), new_vals.reshape((-1,)))
        elif var_name == "channel_exit__x_coordinate":
            self._model.river_x_coordinates = np.append(
                self._model.river_x_coordinates, new_vals
            )
        elif var_name == "channel_exit__y_coordinate":
            self._model.river_y_coordinates = np.append(
                self._model.river_y_coordinates, new_vals
            )

        # Remove duplicate river mouth coordinates (if they exist).
        # This seems clunky... must be better way to get values without
        # duplicating each time?
        # if (self._model.river_x_coordinates[-1] == self._model.river_x_coordinates[-2] and
        #    self._model.river_y_coordinates[-1] == self._model.river_y_coordinates[-2]):
        #    self._model.river_x_coordinates.pop()
        #    self._model.river_y_coordinates.pop()

    def get_component_name(self):
        """Name of the component."""
        return self._name

    def get_input_var_names(self):
        """Get names of input variables."""
        return self._input_var_names

    def get_output_var_names(self):
        """Get names of output variables."""
        return self._output_var_names

    def get_start_time(self):
        """Start time of model."""
        return 0.

    def get_end_time(self):
        """End time of model."""
        return np.finfo("d").max

    def get_current_time(self):
        """Current time of model."""
        return self._model.time

    def get_time_step(self):
        """Time step of model."""
        return self._model.time_step

    def get_time_units(self):
        """Units of time"""
        return "d"
