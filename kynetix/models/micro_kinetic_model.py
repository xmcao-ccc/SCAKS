import cPickle as cpkl
import logging
import os

from kynetix import mpi_master, mpi_size, mpi_installed
import kynetix.models.kinetic_model as km
import kynetix.descriptors.descriptors as dc
import kynetix.descriptors.component_descriptors as cpdc


class MicroKineticModel(km.KineticModel):

    # {{{
    # Data precision.
    decimal_precision = dc.Integer("decimal_precision", default=100)

    # Perturbation size for numerical jacobian matrix.
    perturbation_size = dc.Float("perturbation_size", default=0.01)

    # Direction of perturbation.
    perturbation_direction = dc.String("perturbation_direction", 
                                       default="right",
                                       candidates=["right", "left"])

    # Archived variables.
    archived_variables = dc.Sequence("archive_data",
                                     default=["steady_state_coverages"],
                                     entry_type=str)

    # Numerical representation.
    numerical_representation = dc.String("numerical_representation",
                                         default="mpmath",
                                         candidates=["mpmath", "gmpy", "sympy"])

    # Rootfinding iterator type.
    rootfinding = dc.String("rootfinding",
                            default="MDNewton",
                            candidates=["MDNewton", "ConstrainedNewton"])

    # Iteration tolerance.
    tolerance = dc.Float("tolerance", default=1e-8)

    # Max iteraction steps.
    max_rootfinding_iterations = dc.Integer("max_rootfinding_iterations",
                                            default=100)

    # Ode integration buffer size.
    ode_buffer_size = dc.Integer("ode_buffer_size", default=500)

    # Ode ouptut interval.
    ode_output_interval = dc.Integer("ode_output_interval", default=200)

    # File to store data.
    data_file = dc.String("data_file", default="data.pkl")

    # Species used for conversion from relative energy to absolute eneergy.
    ref_species = dc.Sequence("ref_species", default=[], entry_type=str)

    # Reference energies used to calculate formation energy.
    ref_energies = dc.Dict("ref_energies", default={})
    # }}}

    def __init__(self, setup_file=None,
                       setup_dict=None,
                       verbosity=logging.INFO):
        """
        Parameters:
        -----------
        setup_file: kinetic model set up file, str.

        setup_dict: A dictionary contains essential setup parameters for kinetic model.
        
        verbosity: logging level, int.

        Example:
        --------
        >>> from kynetix.models.kinetic_model import MicroKineticModel
        >>> model = MicroKineticModel(setup_file="setup.mkm",
                                      verbosity=logging.WARNING)
        """
        super(MicroKineticModel, self).__init__(setup_file, setup_dict, verbosity)

    def run(self, **kwargs):
        """
        Function to solve Micro-kinetic model using Steady State Approxmiation
        to get steady state coverages and turnover frequencies.

        Parameters:
        -----------
        init_cvgs: Initial guess for coverages, tuple of floats.

        correct_energy: add free energy corrections to energy data or not, bool

        solve_ode: solve ODE only or not, bool

        fsolve: use scipy.optimize.fsolve to get low-precision root or not, bool

        coarse_guess: use fsolve to do initial coverages preprocessing or not, bool

        XRC: calculate degree of rate control or nor, bool.

        product_name: Production name of the model, str. e.g. "CH3OH_g"

        data_file: The name of data file, str.

        """
        # {{{
        # Setup default parameters.
        init_cvgs = kwargs.pop("init_cvgs", None)
        relative = kwargs.pop("relative", False)
        correct_energy = kwargs.pop("correct_energy", False)
        solve_ode = kwargs.pop("solve_ode", False)
        fsolve = kwargs.pop("fsolve", False)
        coarse_guess = kwargs.pop("coarse_guess", True)
        XRC = kwargs.pop("XRC", False)
        product_name = kwargs.pop("product_name", None)
        data_file = kwargs.pop("data_file", "./rel_energy.py")

        if kwargs:
            for key in kwargs:
                msg = "Found redundant keyword argument: {}".format(key)
                self._logger.warning(msg)

        if mpi_master:
            self._logger.info('--- Solve Micro-kinetic model ---')

        # Get parser and solver.
        parser = self.__parser
        solver = self.__solver

        # Parse data.
        if mpi_master:
            self._logger.info('reading data...')
        if relative:
            if mpi_master:
                self._logger.info('use relative energy directly...')
        else:
            if mpi_master:
                self._logger.info('convert relative to absolute energy...')
        parser.parse_data(filename=data_file, relative=relative)

        # -- solve steady state coverages --
        if mpi_master:
            self._logger.info('passing data to solver...')
        solver.get_data()

        # solve ODE
        # !! do ODE integration AFTER passing data to solver !!
        if solve_ode:
            if mpi_master:
                self._logger.info("initial coverages = %s", str(init_cvgs))
            solver.solve_ode(initial_cvgs=init_cvgs)
            return

        # set initial guess(initial coverage)
        # if there is converged coverage in current path,
        # use it as initial guess
        if init_cvgs:
            # Check init_cvgs type.
            if not isinstance(init_cvgs, (tuple, list)):
                msg = "init_cvgs must be a list or tuple, but {} received."
                msg = msg.format(type(init_cvgs))
                raise ParameterError(msg)

            # Check coverages length.
            if len(init_cvgs) != len(self.__adsorbate_names):
                msg = "init_cvgs must have {} elements, but {} is supplied"
                msg = msg.format(len(self.__adsorbate_names), len(init_cvgs))
                raise ParameterError(msg)

            if mpi_master:
                self._logger.info('use user-defined coverages as initial guess...')

        elif os.path.exists("./data.pkl"):
            with open('data.pkl', 'rb') as f:
                data = cpkl.load(f)
            init_guess = 'steady_state_coverage'
            if init_guess in data:
                if mpi_master:
                    self._logger.info('use coverages in data.pkl as initial guess...')
                init_cvgs = data[init_guess]
                coarse_guess = False
            else:
                if mpi_master:
                    self._logger.info('use Boltzmann coverages as initial guess...')
                init_cvgs = solver.boltzmann_coverages()

        else:  # use Boltzmann coverage
            if mpi_master:
                self._logger.info('use Boltzmann coverages as initial guess...')
            init_cvgs = solver.boltzmann_coverages()

        # Solve steady state coverages.
        # Use scipy.optimize.fsolve or not (fast but low-precision).
        if fsolve:
            if mpi_master:
                self._logger.info('using fsolve to get steady state coverages...')
            ss_cvgs = solver.fsolve_steady_state_cvgs(init_cvgs)
        else:
            if coarse_guess:
                if mpi_master:
                    self._logger.info('getting coarse steady state coverages...')
                init_cvgs = solver.coarse_steady_state_cvgs(init_cvgs)  # coarse root
            if mpi_master:
                self._logger.info('getting precise steady state coverages...')
            ss_cvgs = solver.get_steady_state_cvgs(init_cvgs)

        # Get TOFs for gases.
        tofs = solver.get_tof(ss_cvgs)

        # Get reversibilities.
        rf, rr = solver.get_rates(ss_cvgs)
        reversibilities = solver.get_reversibilities(rf, rr)

        # Calculate XRC.
        if XRC:
            if product_name is None:
                raise ParameterError("production name must be provided to get XRC.")
            solver.get_single_XRC(product_name, epsilon=1e-5)

        return
        # }}}

