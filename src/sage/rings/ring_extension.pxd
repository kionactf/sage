from sage.categories.map cimport Map
from sage.rings.ring cimport CommutativeRing, CommutativeAlgebra
from sage.rings.ring_extension cimport RingExtension_class


cdef _common_base(K, L, degree)

cdef class RingExtension_class(CommutativeAlgebra):
    cdef _type
    cdef _backend
    cdef _defining_morphism
    cdef _backend_defining_morphism
    cdef dict _print_options
    cdef bint _import_methods
    # For division
    cdef RingExtension_class _fraction_field
    cdef type _fraction_field_type

    cpdef is_defined_over(self, base)
    cpdef CommutativeRing _check_base(self, CommutativeRing base)
    cpdef _degree_over(self, CommutativeRing base)
    cpdef _is_finite_over(self, CommutativeRing base)
    cpdef _is_free_over(self, CommutativeRing base)
    cdef Map _defining_morphism_fraction_field(self, bint extend_base)


cdef class RingExtensionFractionField(RingExtension_class):
    cdef _ring


cdef class RingExtensionWithBasis(RingExtension_class):
    cdef _basis
    cdef _basis_names
    cdef _basis_latex_names

    cpdef _basis_over(self, CommutativeRing base)
    # cpdef _free_module(self, CommutativeRing base, bint map)


cdef class RingExtensionWithGen(RingExtensionWithBasis):
    cdef _gen
    cdef _name
