"""
Module for wrapped MPI interfaces used in Kynetix.
"""

import logging
from itertools import chain
from functools import wraps

try:
    from mpi4py import MPI
    MPI_INSTALLED = True
except ImportError:
    MPI_INSTALLED = False

import kynetix.descriptors.descriptors as dc


class MPIUtil(object):
    def __init__(self):
        logger_name = 'kynetix.{}'.format(self.__class__.__name__)
        self._logger = logging.getLogger(logger_name)

    def bcast(self, data):
        if MPI_INSTALLED:
            mpi_comm = MPI.COMM_WORLD
            bdata = mpi_comm.bcast(data, root=0)
        else:
            bdata = data
        return bdata

    def barrier(self):
        if MPI_INSTALLED:
            mpi_comm = MPI.COMM_WORLD
            mpi_comm.barrier()

    @dc.Property
    def rank(self):
        if MPI_INSTALLED:
            mpi_comm = MPI.COMM_WORLD
            return mpi_comm.Get_rank()
        else:
            return 0

    @dc.Property
    def size(self):
        if MPI_INSTALLED:
            mpi_comm = MPI.COMM_WORLD
            return mpi_comm.Get_size()
        else:
            return 1

    @dc.Property
    def is_master(self):
        return self.rank == 0

    # Utility methods.
    def split_seq(self, sequence):
        '''
        Split the sequence according to rank and processor number.
        '''
        starts = [i for i in range(0, len(sequence), len(sequence)//self.size)]
        ends = starts[1: ] + [len(sequence)]
        start, end = list(zip(starts, ends))[self.rank]

        return sequence[start: end]

    def split_size(self, size):
        '''
        Split a size number(int) to sub-size number.
        '''
        if size < self.size:
            warn_msg = ('Splitting size({}) is smaller than process ' +
                        'number({}), more processor would be ' +
                        'superflous').format(size, self.size)
            self._logger.warning(warn_msg)
            splited_sizes = [1]*size + [0]*(self.size - size)
        elif size % self.size != 0:
            residual = size % self.size
            splited_sizes = [size // self.size]*self.size
            for i in range(residual):
                splited_sizes[i] += 1
        else:
            splited_sizes = [size // self.size]*self.size

        return splited_sizes[self.rank]

    def merge_seq(self, seq):
        '''
        Gather data in sub-process to root process.
        '''
        if self.size == 1:
            return seq

        mpi_comm = MPI.COMM_WORLD
        merged_seq= mpi_comm.allgather(seq)
        return list(chain(*merged_seq))

mpi = MPIUtil()

def master_only(func):
    '''
    Decorator to limit a function to be called
    only in master process in MPI env.
    '''
    @wraps(func)
    def _call_in_master_proc(*args, **kwargs):
        if mpi.is_master:
            return func(*args, **kwargs)

    return _call_in_master_proc

