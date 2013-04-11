from .base import BaseOp
from ...verifier.descriptors import parseMethodDescriptor
from ..ssa_types import verifierToSSAType, SSA_MONAD

from .. import objtypes, constraints

class Invoke(BaseOp):
    def __init__(self, parent, instr, info, args, monad, isThisCtor):
        super(Invoke, self).__init__(parent, [monad]+args, makeException=True)

        self.instruction = instr
        self.target, self.name, self.desc = info
        self.isThisCtor = isThisCtor #whether this is a ctor call for the current class

        vtypes = parseMethodDescriptor(self.desc)[1]

        if vtypes:
            stype = verifierToSSAType(vtypes[0])
            cat = len(vtypes)

            self.rval = parent.makeVariable(stype, origin=self)
            self.returned = [self.rval] + [None]*(cat-1)
        else:
            self.rval, self.returned = None, []
        self.outMonad = parent.makeVariable(SSA_MONAD, origin=self)

        # just use a fixed constraint until we can do interprocedural analysis
        # output order is rval, exception, monad, defined by BaseOp.getOutputs
        env = parent.env

        self.mout = constraints.DUMMY
        self.eout = constraints.ObjectConstraint.fromTops(env, [objtypes.ThrowableTT], [])
        if self.rval is not None:
            self.rout = constraints.fromVariable(env, self.rval)

    def propagateConstraints(self, *incons):
        if self.rval is None:
            return self.eout, self.mout
        return self.rout, self.eout, self.mout