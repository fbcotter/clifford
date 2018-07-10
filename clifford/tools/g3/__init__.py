
from clifford.g3c import *
import clifford as cf
import math
import numpy as np

I3 = e123


def quaternion_to_rotor(quaternion):
    """
    Converts a quaternion into a pure rotation rotor
    """
    quat_W = quaternion[0]
    quat_X = quaternion[1]
    quat_Y = quaternion[2]
    quat_Z = quaternion[3]
    i = e23
    j = e13
    k = e12
    return quat_W + quat_X * i + quat_Y * j + quat_Z * k


def rotor_to_quaternion(rotor):
    """
    Converts a pure rotation rotor into a quaternion
    """
    quat = np.zeros(4)
    quat[0] = rotor[0]
    quat[1] = rotor[(2, 3)]
    quat[2] = rotor[(1, 3)]
    quat[3] = rotor[(1, 2)]
    return quat


def quaternion_to_matrix(q):
    """
    Converts a quaternion into a rotation matrix
    """
    qz2 = 2*q[3]**2
    qy2 = 2*q[2]**2
    qx2 = 2*q[1]**2
    qxy = 2*q[1]*q[2]
    qxz = 2*q[1]*q[3]
    qxw = 2*q[1]*q[0]
    qyw = 2*q[2]*q[0]
    qyz = 2*q[2]*q[3]
    qzw = 2*q[3]*q[0]
    return np.array([[1-qy2-qz2, qxy-qzw, qxz+qyw],[qxy+qzw , 1-qx2-qz2, qyz-qxw],[qxz-qyw, qyz+qxw, 1-qx2-qy2]])


def rotor_to_rotation_matrix(R):
    """
    Converts a pure rotation rotor into a rotation matrix
    """
    q = rotor_to_quaternion(R)
    return quaternion_to_matrix(q)


def rotation_matrix_to_quaternion(a):
    """
    Converts a rotation matrix into a quaternion
    """
    trace = a[0][0] + a[1][1] + a[2][2]
    if( trace > 0 ):
        s = 0.5 / math.sqrt(trace+ 1.0)
        w = 0.25 / s
        x = ( a[2][1] - a[1][2] ) * s
        y = ( a[0][2] - a[2][0] ) * s
        z = ( a[1][0] - a[0][1] ) * s
    elif ( a[0][0] > a[1][1] and a[0][0] > a[2][2] ):
        s = 2.0 * math.sqrt( 1.0 + a[0][0] - a[1][1] - a[2][2])
        w = (a[2][1] - a[1][2] ) / s
        x = 0.25 * s
        y = (a[0][1] + a[1][0] ) / s
        z = (a[0][2] + a[2][0] ) / s
    elif (a[1][1] > a[2][2]):
        s = 2.0 * math.sqrt( 1.0 + a[1][1] - a[0][0] - a[2][2])
        w = (a[0][2] - a[2][0] ) / s
        x = (a[0][1] + a[1][0] ) / s
        y = 0.25 * s
        z = (a[1][2] + a[2][1] ) / s
    else:
        s = 2.0 * math.sqrt( 1.0 + a[2][2] - a[0][0] - a[1][1] )
        w = (a[1][0] - a[0][1] ) / s
        x = (a[0][2] + a[2][0] ) / s
        y = (a[1][2] + a[2][1] ) / s
        z = 0.25 * s
    return w,x,y,z


def rotation_matrix_to_rotor(M):
    """
    Converts a rotation matrix into a rotor
    """
    Q = rotation_matrix_to_quaternion(M)
    return quaternion_to_rotor(Q)


def generate_rotation_rotor(theta, euc_vector_m, euc_vector_n):
    """
    Generates a rotation of angle theta in the m, n plane
    """
    euc_vector_n = euc_vector_n / abs(euc_vector_n)
    euc_vector_m = euc_vector_m / abs(euc_vector_m)
    bivector_B = (euc_vector_m ^ euc_vector_n)
    bivector_B = bivector_B / (math.sqrt(-bivector_B * bivector_B))
    rotor = math.cos(theta / 2) - bivector_B * math.sin(theta / 2)
    return rotor


def angle_between_vectors(v1, v2):
    """
    Returns the angle between two conformal vectors
    """
    clipped = np.clip( (v1 | v2)[0], -1.0, 1.0)
    return math.acos(clipped)


def np_to_euc_mv(np_in):
    """ Converts a 3d numpy vector to a 3d GA point """
    return np_in[0]*e1 + np_in[1]*e2 + np_in[2]*e3


def euc_mv_to_np(euc_point):
    """ Converts a 3d GA point to a 3d numpy vector """
    return euc_point[1:4].copy()


def euc_cross_prod(euc_a,euc_b):
    """ Implements the cross product in GA """
    return (-(euc_a^euc_b)*I3).normal()


def random_unit_vector():
    """ Creates a random unit vector """
    return (np_to_euc_mv(np.random.randn(3))).normal()


def random_euc_mv(l_max=10):
    """ Creates a random vector of length uniform up to l_max """
    return l_max*random_unit_vector()*np.random.rand()


def random_rotation_rotor(max_angle=np.pi):
    """ Creates a random rotation rotor """
    return generate_rotation_rotor(max_angle * np.random.rand(), random_unit_vector(), random_unit_vector())


def rotor_vector_to_vector(v1, v2):
    """ Creates a rotor that takes one vector into another """
    if np.sum(np.abs(v1.value - v2.value)) > 0.000001:
        theta = angle_between_vectors(v1, v2)
        return generate_rotation_rotor(theta, v1, v2)
    else:
        mv = cf.MultiVector(layout)
        mv.value[0] = 1.0
        return mv


def correlation_matrix(u_list, v_list):
    """ Creates a correlation matrix between vector lists """
    F_output = np.zeros((3,3))
    for i in range(3):
        for j in range(3):
            for ind in range(len(u_list)):
                u = u_list[ind]
                v = v_list[ind]
                F_output[i,j]+= v[i+1]*u[j+1]
    return F_output


def GA_SVD(u_list, v_list):
    """ Does SVD on a pair of GA vectors """
    F_output = correlation_matrix(u_list, v_list)
    u, s, vh = np.linalg.svd(F_output, full_matrices=True)
    return u, s, vh


def rotation_matrix_align_vecs(u_list, v_list):
    """ Returns the rotation matrix that aligns the set of vectors u and v """
    u, s, vh = GA_SVD(u_list, v_list)
    return np.dot(np.transpose(vh), np.transpose(u))


def rotor_align_vecs(u_list, v_list):
    """ Returns the rotation rotor that aligns the set of vectors u and v """
    M = rotation_matrix_align_vecs(u_list, v_list)
    return rotation_matrix_to_rotor(M)
