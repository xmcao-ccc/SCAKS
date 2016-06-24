import logging
import time
from math import exp

try:
    from KMCLib import *
except ImportError:
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    print "!!!                                                   !!!"
    print "!!!          WARNING: KMCLib is not installed         !!!"
    print "!!! Any kMC calculation using KMCLib will be disabled !!!"
    print "!!!                                                   !!!"
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

from kynetix import __version__
from kynetix.errors.error import *
from kynetix.database.thermo_data import kB_eV
from kynetix.database.lattice_data import *
from kynetix.solvers.solver_base import SolverBase


class KMCSolver(SolverBase):
    def __init__(self, owner):
        '''
        Class for kinetic Monte Carlo simulation process.
        '''
        super(KMCSolver, self).__init__(owner)

        # set logger
        self.__logger = logging.getLogger('model.solvers.KMCSolver')

        # scripting header
        self.__script_header = (
            '# This file was automatically generated by Kynetix' +
            ' (https://github.com/PytLab/Kynetix) powered by KMCLibX.\n' +
            '# Version {}\n# Date: {} \n#\n' +
            '# Do not make changes to this file ' +
            'unless you know what you are doing\n\n').format(__version__, time.asctime())

    def run(self,
            scripting=True,
            trajectory_type="lattice"):
        """
        Run the KMC lattice model simulation with specified parameters.

        Parameters:
        -----------
        scripting: generate lattice script or not, True by default, bool.

        trajectory_type: The type of trajectory to use, the default type is "lattice", str.
                         "xyz" | "lattice". 

        """
        # Get analysis.
        analysis_name = self._owner.analysis()
        if analysis_name:
            analysis = []
            for classname in analysis_name:
                _module = __import__('kmc_plugins', globals(), locals())
                analysis_object = getattr(_module, classname)(self._owner)
                analysis.append(analysis_object)
        else:
            analysis = None

        # Get interactions.
        processes = self._owner.processes()
        interactions = KMCInteractions(processes=processes,
                                       implicit_wildcards=True)

        # Get configuration.
        configuration = self._owner.configuration()

        # Get sitesmap.
        sitesmap = self._owner.sitesmap()

        # Construct KMCLatticeModel object.
        model = KMCLatticeModel(configuration=configuration,
                                sitesmap=sitesmap,
                                interactions=interactions)

        if scripting:
            self.script_lattice_model(model, script_name='kmc_model.py')
            self.__logger.info('script auto_kmc_model.py created.')

        # Get KMCControlParameters.
        control_parameters = self.get_control_parameters()

        # Get trajectory file name.
        trajectory_filename = "auto_{}_trajectory.py".format(trajectory_type)

        # Run KMC main loop.
        model.run(control_parameters=control_parameters,
                  trajectory_filename=trajectory_filename,
                  trajectory_type=trajectory_type,
                  analysis=analysis)

    def get_control_parameters(self):
        """
        Function to get KMCLib KMCControlParameters instance.
        """
        # Get parameters in model.
        nstep = self._owner.nstep()
        dump_interval = self._owner.trajectory_dump_interval()
        seed = self._owner.random_seed()
        rng_type = self._owner.random_generator()
        analysis_interval = self._owner.analysis_interval()

        # KMCLib control parameter instantiation
        control_parameters = KMCControlParameters(number_of_steps=nstep,
                                                  dump_interval=dump_interval,
                                                  analysis_interval=analysis_interval,
                                                  seed=seed,
                                                  rng_type=rng_type)

        return control_parameters

    #-----------------------
    # script KMCLib objects |
    #-----------------------

    def script_decorator(func):
        '''
        Decorator for KMCLib objects scripting.
        Add some essential import statements and save operation.
        '''
        def wrapper(self, obj, script_name=None):
            content = self.__script_header + 'from KMCLib import *\n\n'
            content += func(self, obj)

            # write to file
            if script_name:
                script_name = 'auto_' + script_name
                with open(script_name, 'w') as f:
                    f.write(content)
                self.__logger.info('interactions script written to %s', script_name)

            return content

        return wrapper

    @script_decorator
    def script_lattice_model(self, lattice_model):
        """
        Generate a script representation of lattice model instances.

        Parameters:
        -----------
        lattice_model: The KMCLatticeModel object.

        script_name: filename into which script written, str.
                     set to None by default and no file will be generated.

        Returns:
        --------
        A script that can generate this lattice model object, str.

        """
        content = lattice_model._script()

        return content

    @script_decorator
    def script_configuration(self, configuration):
        '''
        Generate a script representation of interactions instances.

        Parameters:
        -----------
        configuration: The KMCConfiguration object.

        script_name: filename into which script written, str.
                     set to None by default and no file will be generated.

        Returns:
        --------
        A script that can generate this configuration object, str.

        '''
        content = configuration._script()

        return content

    @script_decorator
    def script_interactions(self, interactions):
        '''
        Generate a script representation of interactions instances.

        Parameters:
        -----------
        interactions: The KMCInteractions object.

        script_name: filename into which script written, str.
                     set to None by default and no file will be generated.

        Returns:
        --------
        A script that can generate this interactions object, str.

        '''
        content = interactions._script()

        return content

    @script_decorator
    def script_processes(self, processes):
        '''
        Generate a script representation of processes instances.

        Parameters:
        -----------
        processes: A list of KMCProcess object.

        script_name: filename into which script written, str.
                     set to None by default and no file will be generated.

        Returns:
        --------
        A script that can generate this process object, str.

        '''
        # Get content string.
        content = ''
        for idx, proc in enumerate(processes):
            proc_str = proc._script('process_%d' % idx)
            content += proc_str
        # gather processes
        proc_str = 'processes = [\n'
        for idx in xrange(len(processes)):
            proc_str += (' '*4 + 'process_%d,\n' % idx)
        proc_str += ']\n\n'

        content += proc_str

        return content

