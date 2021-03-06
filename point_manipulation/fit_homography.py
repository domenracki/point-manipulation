import warnings
import numpy as np
from normalize_points import normalize_points

def fit_homography(src, dst, weg=np.array([]), algdist=1):
    """
    Fits a projective transformation between two d-dimensional point sets.
    :param src: Nxd numpy ndarray d-dimensional data points
    :param dst: Nxd numpy ndarray d-dimensional data points
    :param weg: relative weights of data points (Nx1 numpy ndarray)
    :param algdist: [1 (9DOF - default) or 0 (8DOF)] if set to 1 then the algebraic distance ||h||=1 enforcing 9DOF, if set to 0 then h33=1 enforcing 8DOF
    :return: transformation matrix T from src to dst
    """

    # Check input
    if not isinstance(weg, np.ndarray):
        warnings.warn("Input vector weg must be of type numpy.ndarray! weg is of type " + str(type(weg)))
    if algdist != 1 and algdist != 0: algdist = 1

    # -------------------------------
    # Normalize points
    # -------------------------------
    src, Ts = normalize_points(src)
    dst, Td = normalize_points(dst)

    # -------------------------------
    # Set parameters
    # -------------------------------
    # Get number of d-dimensional points
    n = len(src)
    # Check if weights are provided
    if not weg.any():
        weg = np.ones(n)

    # -------------------------------
    # 9 DOF ... ||h|| = 1
    # -------------------------------
    if algdist==1:
        # -------------------------------
        # Construct matrix [A|b]
        # -------------------------------
        A = np.zeros([2*n,9])
        W = np.zeros([2*n,2*n])
        for i in xrange(n):
            # Construct matrix A
            # ax = (x, y, 1, 0, 0, 0, -x'x, -x'y, -x')
            # ay = (0, 0, 0, x, y, 1, -y'x, -y'y, -y')
            A[i*2  ,:] = np.array([ src[i,0], src[i,1], 1, 0, 0, 0, -dst[i,0]*src[i,0], -dst[i,0]*src[i,1], -dst[i,0] ])
            A[i*2+1,:] = np.array([ 0, 0, 0, src[i,0], src[i,1], 1, -dst[i,1]*src[i,0], -dst[i,1]*src[i,1], -dst[i,1] ])
            # Construct diagonal weigh matrix
            W[i*2  ,i*2  ] = weg[i]
            W[i*2+1,i*2+1] = weg[i]
        # -------------------------------
        # Estimate solution H
        # -------------------------------
        # SVD decomposition of weighted matrix A
        _, _, V = np.linalg.svd((A.T.dot(W)).dot(A))
        # Last column vector corresponds to h
        H = np.reshape(V[8],(3,3))

    # -------------------------------
    # 8 DOF ... h33 = 1
    # -------------------------------
    if algdist==0:
        # -------------------------------
        # Construct matrix A and vector b
        # -------------------------------
        A = np.zeros([2*n,8])
        b = np.zeros([2*n,1])
        W = np.zeros([2*n,2*n])
        for i in xrange(n):
            # Construct matrix A
            # ax = (x, y, 1, 0, 0, 0, -x'x, -x'y)
            # ay = (0, 0, 0, x, y, 1, -y'x, -y'y)
            A[i*2  ,:] = np.array([ src[i,0], src[i,1], 1, 0, 0, 0, -dst[i,0]*src[i,0], -dst[i,0]*src[i,1]])
            A[i*2+1,:] = np.array([ 0, 0, 0, src[i,0], src[i,1], 1, -dst[i,1]*src[i,0], -dst[i,1]*src[i,1]])
            # Construct vector b
            b[i*2  ] = dst[i,0]
            b[i*2+1] = dst[i,1]
            # Construct diagonal weigh matrix
            W[i*2  ,i*2  ] = weg[i]
            W[i*2+1,i*2+1] = weg[i]
        # -------------------------------
        # Estimate solution H
        # -------------------------------
        x = np.linalg.solve( (A.T.dot(W)).dot(A) , (A.T.dot(W)).dot(b) )
        H = np.reshape(np.append(x,1),(3,3))

    # -------------------------------
    # Denormalize homography (Td\H*Ts)
    # -------------------------------
    H, _, _, _ = np.linalg.lstsq(Td,H.dot(Ts))

    return H