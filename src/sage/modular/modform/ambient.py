# sage.doctest: needs sage.libs.pari
r"""
Ambient spaces of modular forms

EXAMPLES:

We compute a basis for the ambient space
`M_2(\Gamma_1(25),\chi)`, where `\chi` is
quadratic.

::

    sage: chi = DirichletGroup(25,QQ).0; chi
    Dirichlet character modulo 25 of conductor 5 mapping 2 |--> -1
    sage: n = ModularForms(chi,2); n
    Modular Forms space of dimension 6, character [-1] and weight 2 over Rational Field
    sage: type(n)
    <class 'sage.modular.modform.ambient_eps.ModularFormsAmbient_eps_with_category'>

Compute a basis::

    sage: n.basis()
    [1 + O(q^6),
     q + O(q^6),
     q^2 + O(q^6),
     q^3 + O(q^6),
     q^4 + O(q^6),
     q^5 + O(q^6)]

Compute the same basis but to higher precision::

    sage: n.set_precision(20)
    sage: n.basis()
    [1 + 10*q^10 + 20*q^15 + O(q^20),
     q + 5*q^6 + q^9 + 12*q^11 - 3*q^14 + 17*q^16 + 8*q^19 + O(q^20),
     q^2 + 4*q^7 - q^8 + 8*q^12 + 2*q^13 + 10*q^17 - 5*q^18 + O(q^20),
     q^3 + q^7 + 3*q^8 - q^12 + 5*q^13 + 3*q^17 + 6*q^18 + O(q^20),
     q^4 - q^6 + 2*q^9 + 3*q^14 - 2*q^16 + 4*q^19 + O(q^20),
     q^5 + q^10 + 2*q^15 + O(q^20)]

TESTS::

    sage: m = ModularForms(Gamma1(20),2,GF(7))
    sage: loads(dumps(m)) == m
    True

::

    sage: m = ModularForms(GammaH(11,[3]), 2); m
    Modular Forms space of dimension 2 for Congruence Subgroup Gamma_H(11) with H generated by [3] of weight 2 over Rational Field
    sage: type(m)
    <class 'sage.modular.modform.ambient_g1.ModularFormsAmbient_gH_Q_with_category'>
    sage: m == loads(dumps(m))
    True
"""

# ****************************************************************************
#       Copyright (C) 2006 William Stein <wstein@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  https://www.gnu.org/licenses/
# ****************************************************************************

from sage.arith.misc import is_prime, sigma
from sage.matrix.constructor import matrix
from sage.misc.cachefunc import cached_method
from sage.modular.arithgroup.all import CongruenceSubgroupBase, Gamma0_class, Gamma1_class
from sage.modular.dirichlet import TrivialCharacter
from sage.modular.hecke.ambient_module import AmbientHeckeModule
from sage.modular.modsym.modsym import ModularSymbols
from sage.modules.free_module import VectorSpace
from sage.rings.integer import Integer
from sage.structure.sequence import Sequence

from . import defaults
from . import eisenstein_submodule
from . import eis_series
from . import space
from . import submodule


class ModularFormsAmbient(space.ModularFormsSpace,
                          AmbientHeckeModule):
    """
    An ambient space of modular forms.
    """
    def __init__(self, group, weight, base_ring, character=None, eis_only=False):
        """
        Create an ambient space of modular forms.

        EXAMPLES::

            sage: m = ModularForms(Gamma1(20),20); m
            Modular Forms space of dimension 238 for Congruence Subgroup Gamma1(20) of weight 20 over Rational Field
            sage: m.is_ambient()
            True
        """
        if not isinstance(group, CongruenceSubgroupBase):
            raise TypeError('group (=%s) must be a congruence subgroup' % group)
        weight = Integer(weight)

        if character is None and isinstance(group, Gamma0_class):
            character = TrivialCharacter(group.level(), base_ring)

        self._eis_only = eis_only
        space.ModularFormsSpace.__init__(self, group, weight, character, base_ring)
        if eis_only:
            d = self._dim_eisenstein()
        else:
            d = self.dimension()
        AmbientHeckeModule.__init__(self, base_ring, d, group.level(), weight)

    def _repr_(self):
        """
        Return string representation of ``self``.

        EXAMPLES::

            sage: m = ModularForms(Gamma1(20),100); m._repr_()
            'Modular Forms space of dimension 1198 for Congruence Subgroup Gamma1(20) of weight 100 over Rational Field'

        The output of _repr_ is not affected by renaming the space::

            sage: m.rename('A big modform space')
            sage: m
            A big modform space
            sage: m._repr_()
            'Modular Forms space of dimension 1198 for Congruence Subgroup Gamma1(20) of weight 100 over Rational Field'
        """
        if self._eis_only:
            return "Modular Forms space for %s of weight %s over %s" % (
                self.group(), self.weight(), self.base_ring())
        else:
            return "Modular Forms space of dimension %s for %s of weight %s over %s" % (
                self.dimension(), self.group(), self.weight(), self.base_ring())

    def _submodule_class(self):
        """
        Return the Python class of submodules of this modular forms space.

        EXAMPLES::

            sage: m = ModularForms(Gamma0(20),2)
            sage: m._submodule_class()
            <class 'sage.modular.modform.submodule.ModularFormsSubmodule'>
        """
        return submodule.ModularFormsSubmodule

    def change_ring(self, base_ring):
        """
        Change the base ring of this space of modular forms.

        INPUT:

        - ``R`` -- ring

        EXAMPLES::

            sage: M = ModularForms(Gamma0(37),2)
            sage: M.basis()
            [q + q^3 - 2*q^4 + O(q^6),
             q^2 + 2*q^3 - 2*q^4 + q^5 + O(q^6),
             1 + 2/3*q + 2*q^2 + 8/3*q^3 + 14/3*q^4 + 4*q^5 + O(q^6)]

        The basis after changing the base ring is the reduction modulo
        `3` of an integral basis.

        ::

            sage: M3 = M.change_ring(GF(3))
            sage: M3.basis()
            [q + q^3 + q^4 + O(q^6),
             q^2 + 2*q^3 + q^4 + q^5 + O(q^6),
             1 + q^3 + q^4 + 2*q^5 + O(q^6)]
        """
        from . import constructor
        M = constructor.ModularForms(self.group(), self.weight(), base_ring, prec=self.prec(), eis_only=self._eis_only)
        return M

    @cached_method
    def dimension(self):
        """
        Return the dimension of this ambient space of modular forms,
        computed using a dimension formula (so it should be reasonably
        fast).

        EXAMPLES::

            sage: m = ModularForms(Gamma1(20),20)
            sage: m.dimension()
            238
        """
        return self._dim_eisenstein() + self._dim_cuspidal()

    def hecke_module_of_level(self, N):
        r"""
        Return the Hecke module of level N corresponding to self, which is the
        domain or codomain of a degeneracy map from ``self``. Here N must be either
        a divisor or a multiple of the level of ``self``.

        EXAMPLES::

            sage: ModularForms(25, 6).hecke_module_of_level(5)
            Modular Forms space of dimension 3 for Congruence Subgroup Gamma0(5) of weight 6 over Rational Field
            sage: ModularForms(Gamma1(4), 3).hecke_module_of_level(8)
            Modular Forms space of dimension 7 for Congruence Subgroup Gamma1(8) of weight 3 over Rational Field
            sage: ModularForms(Gamma1(4), 3).hecke_module_of_level(9)
            Traceback (most recent call last):
            ...
            ValueError: N (=9) must be a divisor or a multiple of the level of self (=4)
        """
        if not (N % self.level() == 0 or self.level() % N == 0):
            raise ValueError("N (=%s) must be a divisor or a multiple of the level of self (=%s)" % (N, self.level()))
        from . import constructor
        return constructor.ModularForms(self.group()._new_group_from_level(N), self.weight(), self.base_ring(), prec=self.prec())

    def _degeneracy_raising_matrix(self, M, t):
        r"""
        Calculate the matrix of the degeneracy map from ``self`` to M corresponding
        to `f(q) \mapsto f(q^t)`. Here the level of M should be a multiple of
        the level of self, and t should divide the quotient.

        EXAMPLES::

            sage: ModularForms(22, 2)._degeneracy_raising_matrix(ModularForms(44, 2), 1)
            [  1   0  -1  -2   0   0   0   0   0]
            [  0   1   0  -2   0   0   0   0   0]
            [  0   0   0   0   1   0   0   0  24]
            [  0   0   0   0   0   1   0  -2  21]
            [  0   0   0   0   0   0   1   3 -10]
            sage: ModularForms(22, 2)._degeneracy_raising_matrix(ModularForms(44, 2), 2)
            [0 1 0 0 0 0 0 0 0]
            [0 0 0 1 0 0 0 0 0]
            [0 0 0 0 1 0 0 0 0]
            [0 0 0 0 0 0 1 0 0]
            [0 0 0 0 0 0 0 1 0]
        """
        from sage.matrix.matrix_space import MatrixSpace
        A = MatrixSpace(self.base_ring(), self.dimension(), M.dimension())
        d = M.sturm_bound() + 1
        q = self.an_element().qexp(d).parent().gen()
        im_gens = []
        for x in self.basis():
            fq = x.qexp(d)
            fqt = fq(q**t).add_bigoh(d)  # silly workaround for trac #5367
            im_gens.append(M(fqt))
        return A([M.coordinate_vector(u) for u in im_gens])

    def rank(self):
        r"""
        This is a synonym for ``self.dimension()``.

        EXAMPLES::

            sage: m = ModularForms(Gamma0(20),4)
            sage: m.rank()
            12
            sage: m.dimension()
            12
        """
        return self.dimension()

    def ambient_space(self):
        """
        Return the ambient space that contains this ambient space. This is,
        of course, just this space again.

        EXAMPLES::

            sage: m = ModularForms(Gamma0(3),30)
            sage: m.ambient_space() is m
            True
        """
        return self

    def is_ambient(self):
        """
        Return ``True`` if this an ambient space of modular forms.

        This is an ambient space, so this function always returns ``True``.

        EXAMPLES::

            sage: ModularForms(11).is_ambient()
            True
            sage: CuspForms(11).is_ambient()
            False
        """
        return True

    @cached_method(key=lambda self, sign: Integer(sign))  # convert sign to an Integer before looking this up in the cache
    def modular_symbols(self, sign=0):
        """
        Return the corresponding space of modular symbols with the given
        sign.

        EXAMPLES::

            sage: S = ModularForms(11,2)
            sage: S.modular_symbols()
            Modular Symbols space of dimension 3 for Gamma_0(11) of weight 2 with sign 0 over Rational Field
            sage: S.modular_symbols(sign=1)
            Modular Symbols space of dimension 2 for Gamma_0(11) of weight 2 with sign 1 over Rational Field
            sage: S.modular_symbols(sign=-1)
            Modular Symbols space of dimension 1 for Gamma_0(11) of weight 2 with sign -1 over Rational Field

        ::

            sage: ModularForms(1,12).modular_symbols()
            Modular Symbols space of dimension 3 for Gamma_0(1) of weight 12 with sign 0 over Rational Field
        """
        sign = Integer(sign)
        return ModularSymbols(group=self.group(),
                                     weight=self.weight(),
                                     sign=sign,
                                     base_ring=self.base_ring())

    @cached_method
    def module(self):
        """
        Return the underlying free module corresponding to this space
        of modular forms.

        EXAMPLES::

            sage: m = ModularForms(Gamma1(13),10)
            sage: m.free_module()
            Vector space of dimension 69 over Rational Field
            sage: ModularForms(Gamma1(13),4, GF(49,'b')).free_module()
            Vector space of dimension 27 over Finite Field in b of size 7^2
        """
        d = self.dimension()
        return VectorSpace(self.base_ring(), d)

    # free_module -- stupid thing: there are functions in classes
    # ModularFormsSpace and HeckeModule that both do much the same
    # thing, and one has to override both of them!
    def free_module(self):
        """
        Return the free module underlying this space of modular forms.

        EXAMPLES::

            sage: ModularForms(37).free_module()
            Vector space of dimension 3 over Rational Field
        """
        return self.module()

    def prec(self, new_prec=None):
        """
        Set or get default initial precision for printing modular forms.

        INPUT:

        - ``new_prec`` -- positive integer (default: ``None``)

        OUTPUT: if ``new_prec`` is ``None``, returns the current precision

        EXAMPLES::

            sage: M = ModularForms(1,12, prec=3)
            sage: M.prec()
            3

        ::

            sage: M.basis()
            [q - 24*q^2 + O(q^3), 1 + 65520/691*q + 134250480/691*q^2 + O(q^3)]

        ::

            sage: M.prec(5)
            5
            sage: M.basis()
            [q - 24*q^2 + 252*q^3 - 1472*q^4 + O(q^5),
             1 + 65520/691*q + 134250480/691*q^2 + 11606736960/691*q^3 + 274945048560/691*q^4 + O(q^5)]
        """
        if new_prec:
            self.__prec = new_prec
        try:
            return self.__prec
        except AttributeError:
            self.__prec = defaults.DEFAULT_PRECISION
        return self.__prec

    def set_precision(self, n):
        """
        Set the default precision for displaying elements of this space.

        EXAMPLES::

            sage: m = ModularForms(Gamma1(5),2)
            sage: m.set_precision(10)
            sage: m.basis()
            [1 + 60*q^3 - 120*q^4 + 240*q^5 - 300*q^6 + 300*q^7 - 180*q^9 + O(q^10),
             q + 6*q^3 - 9*q^4 + 27*q^5 - 28*q^6 + 30*q^7 - 11*q^9 + O(q^10),
             q^2 - 4*q^3 + 12*q^4 - 22*q^5 + 30*q^6 - 24*q^7 + 5*q^8 + 18*q^9 + O(q^10)]
            sage: m.set_precision(5)
            sage: m.basis()
            [1 + 60*q^3 - 120*q^4 + O(q^5),
             q + 6*q^3 - 9*q^4 + O(q^5),
             q^2 - 4*q^3 + 12*q^4 + O(q^5)]
        """
        if n < 0:
            raise ValueError("n (=%s) must be >= 0" % n)
        self.__prec = Integer(n)

    ####################################################################
    # Computation of Special Submodules
    ####################################################################
    @cached_method
    def cuspidal_submodule(self):
        """
        Return the cuspidal submodule of this ambient module.

        EXAMPLES::

            sage: ModularForms(Gamma1(13)).cuspidal_submodule()
            Cuspidal subspace of dimension 2 of Modular Forms space of dimension 13 for
            Congruence Subgroup Gamma1(13) of weight 2 over Rational Field
        """
        from .cuspidal_submodule import CuspidalSubmodule
        return CuspidalSubmodule(self)

    @cached_method
    def eisenstein_submodule(self):
        """
        Return the Eisenstein submodule of this ambient module.

        EXAMPLES::

            sage: m = ModularForms(Gamma1(13),2); m
            Modular Forms space of dimension 13 for Congruence Subgroup Gamma1(13) of weight 2 over Rational Field
            sage: m.eisenstein_submodule()
            Eisenstein subspace of dimension 11 of Modular Forms space of dimension 13 for Congruence Subgroup Gamma1(13) of weight 2 over Rational Field
        """
        return eisenstein_submodule.EisensteinSubmodule(self)

    @cached_method(key=lambda self, p: (Integer(p) if p is not None else p))  # convert p to an Integer before looking this up in the cache
    def new_submodule(self, p=None):
        """
        Return the new or `p`-new submodule of this ambient
        module.

        INPUT:

        - ``p`` -- (default: ``None``), if specified return only
          the `p`-new submodule

        EXAMPLES::

            sage: m = ModularForms(Gamma0(33),2); m
            Modular Forms space of dimension 6 for Congruence Subgroup Gamma0(33) of weight 2 over Rational Field
            sage: m.new_submodule()
            Modular Forms subspace of dimension 1 of Modular Forms space of dimension 6 for Congruence Subgroup Gamma0(33) of weight 2 over Rational Field

        Another example::

            sage: M = ModularForms(17,4)
            sage: N = M.new_subspace(); N
            Modular Forms subspace of dimension 4 of Modular Forms space of dimension 6 for Congruence Subgroup Gamma0(17) of weight 4 over Rational Field
            sage: N.basis()
            [q + 2*q^5 + O(q^6),
             q^2 - 3/2*q^5 + O(q^6),
             q^3 + O(q^6),
             q^4 - 1/2*q^5 + O(q^6)]

        ::

            sage: ModularForms(12,4).new_submodule()
            Modular Forms subspace of dimension 1 of Modular Forms space of dimension 9 for Congruence Subgroup Gamma0(12) of weight 4 over Rational Field

        Unfortunately (TODO) - `p`-new submodules aren't yet
        implemented::

            sage: m.new_submodule(3)            # not implemented
            Traceback (most recent call last):
            ...
            NotImplementedError
            sage: m.new_submodule(11)           # not implemented
            Traceback (most recent call last):
            ...
            NotImplementedError
        """
        if p is not None:
            p = Integer(p)
            if not p.is_prime():
                raise ValueError("p (=%s) must be a prime or None." % p)
        return self.cuspidal_submodule().new_submodule(p) + self.eisenstein_submodule().new_submodule(p)

    def _q_expansion(self, element, prec):
        r"""
        Return the `q`-expansion of a particular element of this space of
        modular forms, where the element should be a vector, list, or tuple
        (not a ModularFormElement). Here element should have length =
        self.dimension(). If element = [ a_i ] and self.basis() = [ v_i
        ], then we return `\sum a_i v_i`.

        INPUT:

        - ``element`` -- vector, list or tuple

        - ``prec`` -- desired precision of `q`-expansion

        EXAMPLES::

            sage: m = ModularForms(Gamma0(23),2); m
            Modular Forms space of dimension 3 for Congruence Subgroup Gamma0(23) of weight 2 over Rational Field
            sage: m.basis()
            [q - q^3 - q^4 + O(q^6),
             q^2 - 2*q^3 - q^4 + 2*q^5 + O(q^6),
             1 + 12/11*q + 36/11*q^2 + 48/11*q^3 + 84/11*q^4 + 72/11*q^5 + O(q^6)]
            sage: m._q_expansion([1,2,0], 5)
            q + 2*q^2 - 5*q^3 - 3*q^4 + O(q^5)
        """
        B = self.q_expansion_basis(prec)
        f = self._q_expansion_zero()
        for i in range(len(element)):
            if element[i]:
                f += element[i] * B[i]
        return f

    ####################################################################
    # Computations of Dimensions
    ####################################################################
    @cached_method
    def _dim_cuspidal(self):
        r"""
        Return the dimension of the cuspidal subspace of this ambient
        modular forms space.

        For weights `k \ge 2` this is computed using a
        dimension formula. For weight 1, it will trigger a computation of a
        basis of `q`-expansions using Schaeffer's algorithm, unless this space
        is a space of Eisenstein forms only, in which case we just return 0.

        EXAMPLES::

            sage: m = ModularForms(GammaH(11,[3]), 2); m
            Modular Forms space of dimension 2 for Congruence Subgroup Gamma_H(11) with H generated by [3] of weight 2 over Rational Field
            sage: m._dim_cuspidal()
            1
            sage: m = ModularForms(DirichletGroup(389,CyclotomicField(4)).0,3); m._dim_cuspidal()
            64
            sage: m = ModularForms(GammaH(31, [7]), 1)
            sage: m._dim_cuspidal()
            1
            sage: m = ModularForms(GammaH(31, [7]), 1, eis_only=True)
            sage: m._dim_cuspidal()
            0
        """
        if self._eis_only:
            return 0
        if isinstance(self.group(), Gamma1_class) and self.character() is not None:
            return self.group().dimension_cusp_forms(self.weight(),
                                                     self.character())
        else:
            return self.group().dimension_cusp_forms(self.weight())

    @cached_method
    def _dim_eisenstein(self):
        """
        Return the dimension of the Eisenstein subspace of this modular
        symbols space, computed using a dimension formula.

        EXAMPLES::

            sage: m = ModularForms(GammaH(13,[4]), 2); m
            Modular Forms space of dimension 3 for Congruence Subgroup Gamma_H(13) with H generated by [4] of weight 2 over Rational Field
            sage: m._dim_eisenstein()
            3

            sage: m = ModularForms(DirichletGroup(13).0,7); m
            Modular Forms space of dimension 8, character [zeta12] and weight 7 over Cyclotomic Field of order 12 and degree 4
            sage: m._dim_eisenstein()
            2
            sage: m._dim_cuspidal()
            6

        Test that :issue:`24030` is fixed::

            sage: ModularForms(GammaH(40, [21]), 1).dimension() # indirect doctest
            16
        """
        if isinstance(self.group(), Gamma1_class) and self.character() is not None:
            return self.group().dimension_eis(self.weight(), self.character())
        else:
            return self.group().dimension_eis(self.weight())

    @cached_method
    def _dim_new_cuspidal(self):
        """
        Return the dimension of the new cuspidal subspace, computed using
        dimension formulas.

        EXAMPLES::

            sage: m = ModularForms(GammaH(11,[2]), 2); m._dim_new_cuspidal()
            1
            sage: m = ModularForms(DirichletGroup(33).0,7); m
            Modular Forms space of dimension 26, character [-1, 1] and weight 7 over Rational Field
            sage: m._dim_new_cuspidal()
            20
            sage: m._dim_cuspidal()
            22
        """
        if isinstance(self.group(), Gamma1_class) and self.character() is not None:
            return self.group().dimension_new_cusp_forms(self.weight(), self.character())
        else:
            return self.group().dimension_new_cusp_forms(self.weight())

    @cached_method
    def _dim_new_eisenstein(self):
        """
        Return the dimension of the new Eisenstein subspace, computed
        by enumerating all Eisenstein series of the appropriate level.

        EXAMPLES::

            sage: m = ModularForms(Gamma0(11), 4)
            sage: m._dim_new_eisenstein()
            0
            sage: m = ModularForms(Gamma0(11), 2)
            sage: m._dim_new_eisenstein()
            1
            sage: m = ModularForms(DirichletGroup(36).0,5); m
            Modular Forms space of dimension 28, character [-1, 1] and weight 5 over Rational Field
            sage: m._dim_new_eisenstein()
            2
            sage: m._dim_eisenstein()
            8
        """
        if isinstance(self.group(), Gamma0_class) and self.weight() == 2:
            if is_prime(self.level()):
                d = 1
            else:
                d = 0
        else:
            E = self.eisenstein_series()
            d = len([g for g in E if g.new_level() == self.level()])
        return d

    ####################################################################
    # Computations of all Eisenstein series in self
    ####################################################################

    @cached_method
    def eisenstein_params(self):
        """
        Return parameters that define all Eisenstein series in ``self``.

        OUTPUT: an immutable Sequence

        EXAMPLES::

            sage: m = ModularForms(Gamma0(22), 2)
            sage: v = m.eisenstein_params(); v
            [(Dirichlet character modulo 22 of conductor 1 mapping 13 |--> 1, Dirichlet character modulo 22 of conductor 1 mapping 13 |--> 1, 2), (Dirichlet character modulo 22 of conductor 1 mapping 13 |--> 1, Dirichlet character modulo 22 of conductor 1 mapping 13 |--> 1, 11), (Dirichlet character modulo 22 of conductor 1 mapping 13 |--> 1, Dirichlet character modulo 22 of conductor 1 mapping 13 |--> 1, 22)]
            sage: type(v)
            <class 'sage.structure.sequence.Sequence_generic'>
        """
        eps = self.character()
        if eps is None:
            if isinstance(self.group(), Gamma1_class):
                eps = self.level()
            else:
                raise NotImplementedError
        params = eis_series.compute_eisenstein_params(eps, self.weight())
        return Sequence(params, immutable=True)

    def eisenstein_series(self):
        """
        Return all Eisenstein series associated to this space.

        ::

            sage: ModularForms(27,2).eisenstein_series()
            [q^3 + O(q^6),
             q - 3*q^2 + 7*q^4 - 6*q^5 + O(q^6),
             1/12 + q + 3*q^2 + q^3 + 7*q^4 + 6*q^5 + O(q^6),
             1/3 + q + 3*q^2 + 4*q^3 + 7*q^4 + 6*q^5 + O(q^6),
             13/12 + q + 3*q^2 + 4*q^3 + 7*q^4 + 6*q^5 + O(q^6)]

        ::

            sage: ModularForms(Gamma1(5),3).eisenstein_series()
            [-1/5*zeta4 - 2/5 + q + (4*zeta4 + 1)*q^2 + (-9*zeta4 + 1)*q^3 + (4*zeta4 - 15)*q^4 + q^5 + O(q^6),
             q + (zeta4 + 4)*q^2 + (-zeta4 + 9)*q^3 + (4*zeta4 + 15)*q^4 + 25*q^5 + O(q^6),
             1/5*zeta4 - 2/5 + q + (-4*zeta4 + 1)*q^2 + (9*zeta4 + 1)*q^3 + (-4*zeta4 - 15)*q^4 + q^5 + O(q^6),
             q + (-zeta4 + 4)*q^2 + (zeta4 + 9)*q^3 + (-4*zeta4 + 15)*q^4 + 25*q^5 + O(q^6)]

        ::

            sage: eps = DirichletGroup(13).0^2
            sage: ModularForms(eps,2).eisenstein_series()
            [-7/13*zeta6 - 11/13 + q + (2*zeta6 + 1)*q^2 + (-3*zeta6 + 1)*q^3 + (6*zeta6 - 3)*q^4 - 4*q^5 + O(q^6),
             q + (zeta6 + 2)*q^2 + (-zeta6 + 3)*q^3 + (3*zeta6 + 3)*q^4 + 4*q^5 + O(q^6)]
        """
        return self.eisenstein_submodule().eisenstein_series()

    def _compute_q_expansion_basis(self, prec):
        """
        EXAMPLES::

            sage: m = ModularForms(11,4)
            sage: m._compute_q_expansion_basis(5)
            [q + 3*q^3 - 6*q^4 + O(q^5), q^2 - 4*q^3 + 2*q^4 + O(q^5), 1 + O(q^5), q + 9*q^2 + 28*q^3 + 73*q^4 + O(q^5)]
        """
        S = self.cuspidal_submodule()
        E = self.eisenstein_submodule()
        B_S = S._compute_q_expansion_basis(prec)
        B_E = E._compute_q_expansion_basis(prec)
        return B_S + B_E

    def _compute_hecke_matrix(self, n):
        """
        Compute the matrix of the Hecke operator `T_n` acting on ``self``.

        .. NOTE::

            If ``self`` is a level 1 space, the much faster Victor Miller basis
            is used for this computation.

        EXAMPLES::

            sage: M = ModularForms(11, 2)
            sage: M._compute_hecke_matrix(6)
            [ 2  0]
            [ 0 12]

        Check that :issue:`22780` is fixed::

            sage: M = ModularForms(1, 12)
            sage: M._compute_hecke_matrix(2)
            [ -24    0]
            [   0 2049]
            sage: ModularForms(1, 2).hecke_matrix(2)
            []

        TESTS:

        The following Hecke matrix is 43x43 with very large integer entries.
        We test it indirectly by computing the product and the sum of its
        eigenvalues, and reducing these two integers modulo all the primes
        less than 100::

            sage: M = ModularForms(1, 512)
            sage: t = M._compute_hecke_matrix(5)     # long time (2s)
            sage: t[-1, -1] == 1 + 5^511             # long time (0s, depends on above)
            True
            sage: f = t.charpoly()                   # long time (4s)
            sage: [f[0]%p for p in prime_range(100)] # long time (0s, depends on above)
            [0, 0, 0, 0, 1, 9, 2, 7, 0, 0, 0, 0, 1, 12, 9, 16, 37, 0, 21, 11, 70, 22, 0, 58, 76]
            sage: [f[42]%p for p in prime_range(100)] # long time (0s, depends on above)
            [0, 0, 4, 0, 10, 4, 4, 8, 12, 1, 23, 13, 10, 27, 20, 13, 16, 59, 53, 41, 11, 13, 12, 6, 82]
        """
        if self.level() == 1:
            k = self.weight()
            d = self.dimension()
            if d == 0:
                return matrix(self.base_ring(), 0, 0, [])
            from sage.modular.all import victor_miller_basis, hecke_operator_on_basis
            vmb = victor_miller_basis(k, prec=d * n + 1)[1:]
            Tcusp = hecke_operator_on_basis(vmb, n, k)
            return Tcusp.block_sum(matrix(self.base_ring(), 1, 1,
                                          [sigma(n, k - 1)]))
        else:
            return space.ModularFormsSpace._compute_hecke_matrix(self, n)

    def _compute_hecke_matrix_prime_power(self, p, r):
        r"""
        Compute the Hecke matrix `T_{p^r}`, where `p` is prime and `r \ge 2`.

        This is an internal method.  End users are encouraged to use the
        method hecke_matrix() instead.

        TESTS:

            sage: M = ModularForms(1, 12)
            sage: M._compute_hecke_matrix_prime_power(5, 3)
            [           -359001100500                        0]
            [                       0 116415324211120654296876]
            sage: delta_qexp(126)[125]
            -359001100500
            sage: eisenstein_series_qexp(12, 126)[125]
            116415324211120654296876
        """
        if self.level() == 1:
            return self._compute_hecke_matrix(p**r)
        else:
            return space.ModularFormsSpace._compute_hecke_matrix_prime_power(self, p, r)

    def hecke_polynomial(self, n, var='x'):
        r"""
        Compute the characteristic polynomial of the Hecke operator `T_n` acting
        on this space. Except in level 1, this is computed via modular symbols,
        and in particular is faster to compute than the matrix itself.

        EXAMPLES::

            sage: ModularForms(17,4).hecke_polynomial(2)
            x^6 - 16*x^5 + 18*x^4 + 608*x^3 - 1371*x^2 - 4968*x + 7776

        Check that this gives the same answer as computing the actual Hecke
        matrix (which is generally slower)::

            sage: ModularForms(17,4).hecke_matrix(2).charpoly()
            x^6 - 16*x^5 + 18*x^4 + 608*x^3 - 1371*x^2 - 4968*x + 7776
        """
        return self.cuspidal_submodule().hecke_polynomial(n, var) * self.eisenstein_submodule().hecke_polynomial(n, var)
