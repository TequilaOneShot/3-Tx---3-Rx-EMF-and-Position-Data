import numpy as np

def euler_to_quat_zyx(ex_deg, ey_deg, ez_deg):
    """Converts Z-Y-X Euler angles (degrees) to a Quaternion [w, x, y, z]."""
    hx = np.radians(ex_deg / 2.0)
    hy = np.radians(ey_deg / 2.0)
    hz = np.radians(ez_deg / 2.0)

    cx, sx = np.cos(hx), np.sin(hx)
    cy, sy = np.cos(hy), np.sin(hy)
    cz, sz = np.cos(hz), np.sin(hz)

    w = cx * cy * cz + sx * sy * sz
    x = sx * cy * cz - cx * sy * sz
    y = cx * sy * cz + sx * cy * sz
    z = cx * cy * sz - sx * sy * cz
    return np.array([w, x, y, z])

def quat_inv(q):
    """Computes the inverse of a quaternion [w, x, y, z]."""
    w, x, y, z = q
    norm_sq = w**2 + x**2 + y**2 + z**2
    return np.array([w, -x, -y, -z]) / norm_sq

def quat_mul(q1, q2):
    """Multiplies two quaternions q1 * q2."""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2
    return np.array([w, x, y, z])

def quat_to_euler_zyx(q):
    """Converts a Quaternion [w, x, y, z] back to Z-Y-X Euler angles (degrees)."""
    w, x, y, z = q

    # Pitch (Y)
    sin_y = 2.0 * (w * y - z * x)
    
    # Check for vectorized numpy array processing vs scalar processing
    if np.isscalar(sin_y):
        if sin_y >= 1.0:
            py = np.pi / 2.0
        elif sin_y <= -1.0:
            py = -np.pi / 2.0
        else:
            py = np.arcsin(sin_y)
    else:
        sin_y = np.clip(sin_y, -1.0, 1.0)
        py = np.arcsin(sin_y)

    # Roll (X)
    roll = np.arctan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x**2 + y**2))

    # Yaw (Z)
    yaw = np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y**2 + z**2))

    return np.degrees(roll), np.degrees(py), np.degrees(yaw)

def get_true_relative_tilt(ex_curr, ey_curr, ez_curr, ex_init, ey_init, ez_init):
    """
    Strips the base offset using Pre-multiplication matching the MATLAB generator,
    returning the true isolated tilt angles (Ex, Ey, Ez).
    """
    q_curr = euler_to_quat_zyx(ex_curr, ey_curr, ez_curr)
    q_init = euler_to_quat_zyx(ex_init, ey_init, ez_init)

    # MATCH GENERATOR: Q_curr = Q_tilt * Q_init  =>  Q_tilt = Q_curr * Q_init_inv
    q_init_inv = quat_inv(q_init)
    q_tilt = quat_mul(q_curr, q_init_inv)

    if np.isscalar(q_tilt[0]):
        if q_tilt[0] < 0:
            q_tilt = -q_tilt
    else:
        q_tilt = np.where(q_tilt[0] < 0, -q_tilt, q_tilt)

    true_ex, true_ey, true_ez = quat_to_euler_zyx(q_tilt)
    return true_ex, true_ey, true_ez

# ==========================================================
# Remove offset from N_samples x 3 array of Roll, Pitch, Yaw
# ==========================================================

# INPUT: ori_in = data[:, 12:15] (from .csv file)
ori_in = np.zeros((10, 3)) # dummy array, replace with actual correct data array
EX_INIT = 179.91
EY_INIT = 0.01
EZ_INIT = 66.28

# Fixed input processing for array formats so it properly replaces the 'ori' dimensions (for use with calibration, training...)
ori_out = np.array(get_true_relative_tilt(
    ori_in[:, 0], ori_in[:, 1], ori_in[:, 2],
    EX_INIT, EY_INIT, EZ_INIT
)).T

# For function testing:
if __name__ == "__main__":
    # Angles read back from the robot pendant photo
    ex_robot = 170.75
    ey_robot = -4.01
    ez_robot = 66.54
    
    true_ex, true_ey, true_ez = get_true_relative_tilt( # remove np.array as only 1 row of angles is needed)
        ex_robot, ey_robot, ez_robot, 
        EX_INIT, EY_INIT, EZ_INIT
    )
    
    print(f"True Relative Ex: {true_ex:.2f}°")
    print(f"True Relative Ey: {true_ey:.2f}°")
    print(f"True Relative Ez: {true_ez:.2f}°")