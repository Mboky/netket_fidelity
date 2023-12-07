from functools import partial
import numpy as np

import jax
import jax.numpy as jnp

from jax.tree_util import register_pytree_node_class

from netket.operator import DiscreteJaxOperator, spin


@register_pytree_node_class
class Rx(DiscreteJaxOperator):
    def __init__(self, hi, idx, angle):
        super().__init__(hi)
        self._local_states = jnp.asarray(hi.local_states)
        self._idx = idx
        self._angle = angle

    @property
    def angle(self):
        """
        The angle of this rotation.
        """
        return self._angle

    @property
    def idx(self):
        """
        The qubit id on which this rotation acts
        """
        return self._idx

    @property
    def dtype(self):
        return complex

    @property
    def H(self):
        return Rx(self.hilbert, self.idx, -self.angle)

    def __eq__(self, o):
        if isinstance(o, Rx):
            return o.idx == self.idx and o.angle == self.angle
        return False

    def tree_flatten(self):
        children = (self.angle,)
        aux_data = (
            self.hilbert,
            self.idx,
        )
        return (children, aux_data)

    @classmethod
    def tree_unflatten(cls, aux_data, children):
        (angle,) = children
        return cls(*aux_data, angle)

    @property
    def max_conn_size(self) -> int:
        return 2

    @jax.jit
    def get_conn_padded(self, x):
        xr = x.reshape(-1, x.shape[-1])
        xp, mels = get_conns_and_mels_Rx(xr, self.idx, self.angle, self._local_states)
        xp = xp.reshape(x.shape[:-1] + xp.shape[-2:])
        mels = mels.reshape(x.shape[:-1] + mels.shape[-1:])
        return xp, mels

    def get_conn_flattened(self, x, sections):
        xp, mels = self.get_conn_padded(x)
        sections[:] = np.arange(2, mels.size + 2, 2)

        xp = xp.reshape(-1, self.hilbert.size)
        mels = mels.reshape(
            -1,
        )
        return xp, mels

    def to_local_operator(self):
        ctheta = np.cos(self.angle / 2)
        stheta = np.sin(self.angle / 2)
        return ctheta - 1j * stheta * spin.sigmax(self.hilbert, self.idx)


@partial(jax.vmap, in_axes=(0, None, None, None), out_axes=(0, 0))
def get_conns_and_mels_Rx(sigma, idx, angle, local_states):
    assert sigma.ndim == 1

    state_0 = jnp.asarray(local_states[0], dtype=sigma.dtype)
    state_1 = jnp.asarray(local_states[1], dtype=sigma.dtype)

    conns = jnp.tile(sigma, (2, 1))
    current_state = sigma[idx]
    flipped_state = jnp.where(current_state == state_0, state_1, state_0)
    conns = conns.at[1, idx].set(flipped_state)

    mels = jnp.zeros(2, dtype=complex)
    mels = mels.at[0].set(jnp.cos(angle / 2))
    mels = mels.at[1].set(-1j * jnp.sin(angle / 2))

    return conns, mels


@register_pytree_node_class
class Ry(DiscreteJaxOperator):
    def __init__(self, hi, idx, angle):
        super().__init__(hi)
        self._local_states = jnp.asarray(hi.local_states)
        self._idx = idx
        self._angle = angle

    @property
    def angle(self):
        """
        The angle of this rotation.
        """
        return self._angle

    @property
    def idx(self):
        """
        The qubit id on which this rotation acts
        """
        return self._idx

    @property
    def dtype(self):
        return complex

    @property
    def H(self):
        return Ry(self.hilbert, self.idx, -self.angle * 2)

    @property
    def max_conn_size(self) -> int:
        return 2

    def __eq__(self, o):
        if isinstance(o, Ry):
            return o.idx == self.idx and o.angle == self.angle
        return False

    def tree_flatten(self):
        children = (self.angle,)
        aux_data = (
            self.hilbert,
            self.idx,
        )
        return (children, aux_data)

    @classmethod
    def tree_unflatten(cls, aux_data, children):
        (angle,) = children
        return cls(*aux_data, angle)

    @jax.jit
    def get_conn_padded(self, x):
        xr = x.reshape(-1, x.shape[-1])
        xp, mels = get_conns_and_mels_Ry(xr, self.idx, self.angle, self._local_states)
        xp = xp.reshape(x.shape[:-1] + xp.shape[-2:])
        mels = mels.reshape(x.shape[:-1] + mels.shape[-1:])
        return xp, mels

    def get_conn_flattened(self, x, sections):
        xp, mels = self.get_conn_padded(x)
        sections[:] = np.arange(2, mels.size + 2, 2)

        xp = xp.reshape(-1, self.hilbert.size)
        mels = mels.reshape(
            -1,
        )
        return xp, mels

    def to_local_operator(self):
        ctheta = np.cos(self.angle / 2)
        stheta = np.sin(self.angle / 2)
        return ctheta + 1j * stheta * spin.sigmay(self.hilbert, self.idx)


@partial(jax.vmap, in_axes=(0, None, None, None), out_axes=(0, 0))
def get_conns_and_mels_Ry(sigma, idx, angle, local_states):
    assert sigma.ndim == 1

    state_0 = jnp.asarray(local_states[0], dtype=sigma.dtype)
    state_1 = jnp.asarray(local_states[1], dtype=sigma.dtype)

    conns = jnp.tile(sigma, (2, 1))
    current_state = sigma[idx]
    flipped_state = jnp.where(current_state == state_0, state_1, state_0)
    conns = conns.at[1, idx].set(flipped_state)

    mels = jnp.zeros(2, dtype=complex)
    mels = mels.at[0].set(jnp.cos(angle / 2))
    phase_factor = jnp.where(conns.at[0, idx].get() == local_states[0], 1, -1)
    mels = mels.at[1].set(phase_factor * jnp.sin(angle / 2))

    return conns, mels


@register_pytree_node_class
class Hadamard(DiscreteJaxOperator):
    def __init__(self, hi, idx):
        super().__init__(hi)
        self._local_states = jnp.asarray(hi.local_states)
        self._idx = idx

    @property
    def idx(self):
        """
        The qubit id on which this hadamard gate acts upon.
        """
        return self._idx

    @property
    def dtype(self):
        return np.float64

    @property
    def H(self):
        return Hadamard(self.hilbert, self.idx)

    def to_local_operator(self):
        sq2 = np.sqrt(2)
        return (
            spin.sigmaz(self.hilbert, self.idx) + spin.sigmax(self.hilbert, self.idx)
        ) / sq2

    def __eq__(self, o):
        if isinstance(o, Hadamard):
            return o.idx == self.idx
        return False

    def tree_flatten(self):
        children = ()
        aux_data = (self.hilbert, self.idx)
        return (children, aux_data)

    @classmethod
    def tree_unflatten(cls, aux_data, children):
        return cls(*aux_data)

    @property
    def max_conn_size(self) -> int:
        return 2

    @jax.jit
    def get_conn_padded(self, x):
        xr = x.reshape(-1, x.shape[-1])
        xp, mels = get_conns_and_mels_Hadamard(xr, self.idx, self._local_states)
        xp = xp.reshape(x.shape[:-1] + xp.shape[-2:])
        mels = mels.reshape(x.shape[:-1] + mels.shape[-1:])
        return xp, mels

    @jax.jit
    def get_conn_flattened(self, x, sections):
        xp, mels = self.get_conn_padded(x)
        sections[:] = np.arange(2, mels.size + 2, 2)

        xp = xp.reshape(-1, self.hilbert.size)
        mels = mels.reshape(
            -1,
        )
        return xp, mels


@partial(jax.vmap, in_axes=(0, None, None), out_axes=(0, 0))
def get_conns_and_mels_Hadamard(sigma, idx, local_states):
    assert sigma.ndim == 1

    state_0 = jnp.asarray(local_states[0], dtype=sigma.dtype)
    state_1 = jnp.asarray(local_states[1], dtype=sigma.dtype)

    conns = jnp.tile(sigma, (2, 1))
    current_state = sigma[idx]
    flipped_state = jnp.where(current_state == state_0, state_1, state_0)
    conns = conns.at[1, idx].set(flipped_state)

    mels = jnp.zeros(2, dtype=float)
    mels = mels.at[1].set(1 / jnp.sqrt(2))
    state_value = conns.at[0, idx].get()
    mels_value = jnp.where(state_value == local_states[0], 1, -1) / jnp.sqrt(2)
    mels = mels.at[0].set(mels_value)

    return conns, mels


@register_pytree_node_class
class Hadamard_multi(DiscreteJaxOperator):
    def __init__(self, hi, idx):
        super().__init__(hi)
        self._local_states = jnp.asarray(hi.local_states)
        self._idx = idx

    @property
    def idx(self):
        """
        The qubit ids on which this hadamard gate acts upon.
        """
        return self._idx

    @property
    def dtype(self):
        return np.float64

    @property
    def H(self):
        return Hadamard_multi(self.hilbert, self.idx)

    def to_local_operator(self):
        pass
        # sq2 = np.sqrt(2)
        # return (
        #     spin.sigmaz(self.hilbert, self.idx) + spin.sigmax(self.hilbert, self.idx)
        # ) / sq2

    def __eq__(self, o):
        if isinstance(o, Hadamard):
            return o.idx == self.idx
        return False

    def tree_flatten(self):
        children = ()
        aux_data = (self.hilbert, self.idx)
        return (children, aux_data)

    @classmethod
    def tree_unflatten(cls, aux_data, children):
        return cls(*aux_data)

    @property
    def max_conn_size(self) -> int:
        return 2 ** len(self.idx)

    @jax.jit
    def get_conn_padded(self, x):
        xr = x.reshape(-1, x.shape[-1])
        xp, mels = get_conns_and_mels_Hadamard_multiple(
            xr, self.idx, self._local_states
        )
        xp = xp.reshape(x.shape[:-1] + xp.shape[-2:])
        mels = mels.reshape(x.shape[:-1] + mels.shape[-1:])
        return xp, mels

    @jax.jit
    def get_conn_flattened(self, x, sections):
        xp, mels = self.get_conn_padded(x)
        sections[:] = np.arange(2, mels.size + 2, 2)

        xp = xp.reshape(-1, self.hilbert.size)
        mels = mels.reshape(
            -1,
        )
        return xp, mels


@partial(jax.vmap, in_axes=(0, None, None), out_axes=(0, 0))
def get_conns_and_mels_Hadamard_multiple(sigma, idx, local_states):
    assert sigma.ndim == 1

    state_0 = jnp.asarray(local_states[0], dtype=sigma.dtype)
    state_1 = jnp.asarray(local_states[1], dtype=sigma.dtype)

    # Determine the number of combinations
    num_combinations = 2 ** len(idx)

    # Initialize conns and mels
    conns = jnp.tile(sigma, (num_combinations, 1))
    mels = jnp.zeros(num_combinations, dtype=float)

    # Iterate over all combinations of flips
    for i in range(num_combinations):
        combination = [idx[j] for j in range(len(idx)) if (i >> j) & 1]
        for index in combination:
            current_state = sigma[index]
            flipped_state = jnp.where(current_state == state_0, state_1, state_0)
            conns = conns.at[i, index].set(flipped_state)

        # Set mels value
        mels_value = jnp.prod(
            jnp.where(conns[i, idx] == local_states[0], 1, -1)
        ) / jnp.sqrt(2 ** len(idx))
        mels = mels.at[i].set(mels_value)

    return conns, mels
