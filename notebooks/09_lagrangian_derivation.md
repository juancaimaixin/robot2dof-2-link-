Link 1 Center of Mass
Link 1 is oriented at \(q_1\); its center of mass lies at distance \(l_{c1}\) from joint 1:
\[
p_{c1}=
\begin{bmatrix}
x_{c1}\\y_{c1}
\end{bmatrix}
=
\begin{bmatrix}
l_{c1}\cos q_1\\
l_{c1}\sin q_1
\end{bmatrix}
\]Link 2 Center of Mass
First move from the base to joint 2:
\[
\begin{bmatrix}
l_1\cos q_1\\
l_1\sin q_1
\end{bmatrix}
\]Then move another \(l_{c2}\) along link 2. Its absolute orientation is \(q_1+q_2\), so:
\[
p_{c2}=
\begin{bmatrix}
l_1\cos q_1+l_{c2}\cos(q_1+q_2)\\
l_1\sin q_1+l_{c2}\sin(q_1+q_2)
\end{bmatrix}
\]The key relationship is:
\[
\text{Absolute angle of link 2}=q_1+q_2
\]Using only cos(q2) and sin(q2) would be incorrect because \(q_2\) is relative to link 1.
Check the nominal parameters at \(q_1=q_2=0\):
\[
p_{c1}=
\begin{bmatrix}
0.25\\0
\end{bmatrix}m
\]\[
p_{c2}=
\begin{bmatrix}
0.50+0.20\\0
\end{bmatrix}
=
\begin{bmatrix}
0.70\\0
\end{bmatrix}m
\]This step records the two center-of-mass positions. Next, differentiate them with respect to time to obtain velocities.

Link 1 Center-of-Mass Velocity
Link 1 center-of-mass position:
\[
p_{c1}=
\begin{bmatrix}
l_{c1}\cos q_1\\
l_{c1}\sin q_1
\end{bmatrix}
\]Using:
\[
\frac{d}{dt}\cos q_1
=
-\sin q_1\dot q_1
\]\[
\frac{d}{dt}\sin q_1
=
\cos q_1\dot q_1
\]We obtain:
\[
\dot p_{c1}=
\begin{bmatrix}
-l_{c1}\sin q_1\dot q_1\\
l_{c1}\cos q_1\dot q_1
\end{bmatrix}
\]Link 2 Center-of-Mass Velocity
Link 2 center-of-mass position:
\[
p_{c2}=
\begin{bmatrix}
l_1\cos q_1+l_{c2}\cos(q_1+q_2)\\
l_1\sin q_1+l_{c2}\sin(q_1+q_2)
\end{bmatrix}
\]The key chain rule is:
\[
\frac{d}{dt}\cos(q_1+q_2)
=
-\sin(q_1+q_2)
(\dot q_1+\dot q_2)
\]Therefore:
\[
\dot p_{c2}=
\begin{bmatrix}
-l_1\sin q_1\dot q_1
-l_{c2}\sin(q_1+q_2)(\dot q_1+\dot q_2)
\\
l_1\cos q_1\dot q_1
+l_{c2}\cos(q_1+q_2)(\dot q_1+\dot q_2)
\end{bmatrix}
\]Here, \(\dot q_1+\dot q_2\) is link 2's absolute angular velocity because its absolute angle is \(q_1+q_2\).
A quick check at the horizontal configuration \(q_1=q_2=0\):
\[
\dot p_{c1}=
\begin{bmatrix}
0\\l_{c1}\dot q_1
\end{bmatrix}
\]\[
\dot p_{c2}=
\begin{bmatrix}
0\\
l_1\dot q_1+
l_{c2}(\dot q_1+\dot q_2)
\end{bmatrix}
\]For small rotations of horizontal links, the instantaneous center-of-mass velocity is vertical, consistent with the geometry.

Rigid-Body Kinetic Energy
Each rigid link's kinetic energy consists of:
\[
T_i
=
\frac12m_i\dot p_{ci}^T\dot p_{ci}
+
\frac12I_i\omega_i^2
\]where:
- The first term is translational kinetic energy of the center of mass.
- The second term is rotational kinetic energy about the center of mass.
- \(\omega_i\) is the link's absolute angular velocity.
The two absolute angular velocities are:
\[
\omega_1=\dot q_1
\]\[
\omega_2=\dot q_1+\dot q_2
\]Link 1 Kinetic Energy
Link 1 center-of-mass velocity:
\[
\dot p_{c1}=
\begin{bmatrix}
-l_{c1}\sin q_1\dot q_1\\
l_{c1}\cos q_1\dot q_1
\end{bmatrix}
\]Squared speed:
\[
\begin{aligned}
\dot p_{c1}^T\dot p_{c1}
&=
l_{c1}^2\sin^2q_1\dot q_1^2
+
l_{c1}^2\cos^2q_1\dot q_1^2\\
&=
l_{c1}^2\dot q_1^2
\end{aligned}
\]Using the identity:
\[
\sin^2q_1+\cos^2q_1=1
\]Therefore:
\[
\boxed{
T_1
=
\frac12
\left(
m_1l_{c1}^2+I_1
\right)
\dot q_1^2
}
\]Link 2 Squared Speed
For compact notation, define:
\[
\dot q_{12}=\dot q_1+\dot q_2
\]Link 2's squared center-of-mass speed simplifies to:
\[
\boxed{
\dot p_{c2}^T\dot p_{c2}
=
l_1^2\dot q_1^2
+
l_{c2}^2\dot q_{12}^2
+
2l_1l_{c2}\cos q_2
\dot q_1\dot q_{12}
}
\]The \(\cos q_2\) in the cross term follows from:
\[
\sin q_1\sin(q_1+q_2)
+
\cos q_1\cos(q_1+q_2)
=
\cos q_2
\]Therefore, link 2's kinetic energy is:
\[
\boxed{
T_2
=
\frac12m_2
\left[
l_1^2\dot q_1^2
+
l_{c2}^2(\dot q_1+\dot q_2)^2
+
2l_1l_{c2}\cos q_2
\dot q_1(\dot q_1+\dot q_2)
\right]
+
\frac12I_2(\dot q_1+\dot q_2)^2
}
\]Total System Kinetic Energy
\[
\boxed{
T=T_1+T_2
}
\]That is:
\[
\begin{aligned}
T={}&
\frac12
(m_1l_{c1}^2+I_1)\dot q_1^2\\
&+
\frac12m_2
\left[
l_1^2\dot q_1^2
+
l_{c2}^2(\dot q_1+\dot q_2)^2
+
2l_1l_{c2}\cos q_2
\dot q_1(\dot q_1+\dot q_2)
\right]\\
&+
\frac12I_2(\dot q_1+\dot q_2)^2
\end{aligned}
\]Kinetic energy is measured in joules:
\[
\mathrm{kg\cdot m^2/s^2}
\]The individual \(\dot q_i\) terms are not expanded yet. Next, derive gravitational potential energy from center-of-mass heights.

## Gravitational Potential Energy

With y upward and gravity downward:

\[
V=mgy
\]

Link 1 center-of-mass height:

\[
y_{c1}=l_{c1}\sin q_1
\]

Link 2 center-of-mass height:

\[
y_{c2}
=
l_1\sin q_1
+
l_{c2}\sin(q_1+q_2)
\]

The links' potential energies are:

\[
V_1=m_1gl_{c1}\sin q_1
\]

\[
V_2=
m_2g
\left[
l_1\sin q_1+
l_{c2}\sin(q_1+q_2)
\right]
\]

Total potential energy:

\[
\boxed{
V=
g\left[
(m_1l_{c1}+m_2l_1)\sin q_1
+
m_2l_{c2}\sin(q_1+q_2)
\right]
}
\]

Lagrangian and Euler-Lagrange Equations
The Lagrangian is defined as:
\[
\boxed{L(q,\dot q)=T(q,\dot q)-V(q)}
\]Each joint satisfies:
\[
\boxed{
\frac{d}{dt}
\left(
\frac{\partial L}{\partial\dot q_i}
\right)
-
\frac{\partial L}{\partial q_i}
=
\tau_i
}
\]The final robot dynamics take the form:
\[
M(q)\ddot q+c(q,\dot q)+G(q)=\tau
\]Because:
\[
L=T-V
\]The potential-energy contribution to the Euler-Lagrange equations is:
\[
-\frac{\partial L}{\partial q}
=
\frac{\partial V}{\partial q}
\]Therefore, define:
\[
\boxed{
G(q)=\frac{\partial V}{\partial q}
}
\]Partial Derivative with Respect to \(q_1\)
Total potential energy:
\[
V=
g\left[
(m_1l_{c1}+m_2l_1)\sin q_1
+
m_2l_{c2}\sin(q_1+q_2)
\right]
\]Using:
\[
\frac{\partial}{\partial q_1}\sin q_1
=
\cos q_1
\]\[
\frac{\partial}{\partial q_1}
\sin(q_1+q_2)
=
\cos(q_1+q_2)
\]We obtain:
\[
\boxed{
G_1(q)
=
g\left[
(m_1l_{c1}+m_2l_1)\cos q_1
+
m_2l_{c2}\cos(q_1+q_2)
\right]
}
\]Partial Derivative with Respect to \(q_2\)
The first term does not contain \(q_2\), so its partial derivative is zero:
\[
\frac{\partial}{\partial q_2}
\left[
(m_1l_{c1}+m_2l_1)\sin q_1
\right]
=0
\]Therefore:
\[
\boxed{
G_2(q)
=
gm_2l_{c2}\cos(q_1+q_2)
}
\]The complete gravity vector is:
\[
\boxed{
G(q)=
\begin{bmatrix}
g[(m_1l_{c1}+m_2l_1)\cos q_1
+m_2l_{c2}\cos(q_1+q_2)]
\\
gm_2l_{c2}\cos(q_1+q_2)
\end{bmatrix}
}
\]Horizontal-Configuration Check
When:
\[
q_1=q_2=0
\]We have:
\[
G_1
=
9.81
[
2.0(0.25)+1.5(0.50)+1.5(0.20)
]
=
15.2055\ \mathrm{N\,m}
\]\[
G_2
=
9.81[1.5(0.20)]
=
2.943\ \mathrm{N\,m}
\]The actuator torque required to hold the arm horizontally at rest is:
\[
\tau=G(q)
=
\begin{bmatrix}
15.2055\\
2.943
\end{bmatrix}
\mathrm{N\,m}
\]The positive sign means the actuators apply counterclockwise torque against downward gravity.
This step derives only \(G(q)\). Next, extract the mass matrix \(M(q)\) from total kinetic energy \(T\).

Matrix Form of Kinetic Energy
Define generalized velocity:
\[
\dot q=
\begin{bmatrix}
\dot q_1\\
\dot q_2
\end{bmatrix}
\]Total robot kinetic energy can be written as:
\[
\boxed{
T=\frac12\dot q^TM(q)\dot q
}
\]For a symmetric matrix:
\[
M=
\begin{bmatrix}
M_{11}&M_{12}\\
M_{12}&M_{22}
\end{bmatrix}
\]Expansion gives:
\[
T=
\frac12M_{11}\dot q_1^2
+
M_{12}\dot q_1\dot q_2
+
\frac12M_{22}\dot q_2^2
\]Expanding the original kinetic energy and comparing the three velocity-term coefficients gives \(M_{11}\), \(M_{12}\), and \(M_{22}\).
Expanding the Velocity Combinations
Using:
\[
(\dot q_1+\dot q_2)^2
=
\dot q_1^2
+
2\dot q_1\dot q_2
+
\dot q_2^2
\]and:
\[
\dot q_1(\dot q_1+\dot q_2)
=
\dot q_1^2+\dot q_1\dot q_2
\]Expand the preceding total kinetic energy and collect coefficients to obtain:
\[
\boxed{
M_{11}
=
I_1+I_2
+m_1l_{c1}^2
+m_2
\left(
l_1^2+l_{c2}^2
+2l_1l_{c2}\cos q_2
\right)
}
\]\[
\boxed{
M_{12}=M_{21}
=
I_2
+
m_2
\left(
l_{c2}^2
+l_1l_{c2}\cos q_2
\right)
}
\]\[
\boxed{
M_{22}
=
I_2+m_2l_{c2}^2
}
\]The complete mass matrix is:
\[
\boxed{
M(q)=
\begin{bmatrix}
I_1+I_2+m_1l_{c1}^2+
m_2(l_1^2+l_{c2}^2+2l_1l_{c2}\cos q_2)
&
I_2+m_2(l_{c2}^2+l_1l_{c2}\cos q_2)
\\
I_2+m_2(l_{c2}^2+l_1l_{c2}\cos q_2)
&
I_2+m_2l_{c2}^2
\end{bmatrix}
}
\]Important Properties
The mass matrix must be symmetric:
\[
M_{12}=M_{21}
\]It depends on \(q_2\), not \(q_1\), because rotating the whole arm does not change the relative geometry governing kinetic energy.
The mass matrix can also be obtained directly as the Hessian of kinetic energy:
\[
\boxed{
M_{ij}
=
\frac{\partial^2T}
{\partial\dot q_i\partial\dot q_j}
}
\]Nominal-Parameter Check
When \(q_2=0\):
\[
M(0)\approx
\begin{bmatrix}
0.9216667&0.23\\
0.23&0.08
\end{bmatrix}
\mathrm{kg\,m^2}
\]This matrix is symmetric. The numerical implementation must also verify positive definiteness at random configurations.
This step records only \(M(q)\). Next, derive the Coriolis and centrifugal vector \(c(q,\dot q)\).

## Coriolis and Centrifugal Vector

Define:

\[
h=m_2l_1l_{c2}\sin q_2
\]

Then:

\[
\boxed{
c(q,\dot q)=
\begin{bmatrix}
-h(2\dot q_1\dot q_2+\dot q_2^2)\\
h\dot q_1^2
\end{bmatrix}
}
\]

## From Euler-Lagrange to the Standard Dynamics Equation

Starting from:

\[
\frac{d}{dt}
\left(
\frac{\partial L}{\partial\dot q_i}
\right)
-
\frac{\partial L}{\partial q_i}
=
\tau_i
\]

Using:

\[
L=T-V
\]

\[
T=\frac12\dot q^TM(q)\dot q
\]

\[
G(q)=\frac{\partial V}{\partial q}
\]

Collect acceleration, quadratic-velocity, and potential-energy terms into:

\[
\boxed{
M(q)\ddot q+c(q,\dot q)+G(q)=\tau
}
\]

where:

- \(M(q)\ddot q\): inertial term.
- \(c(q,\dot q)\): Coriolis and centrifugal term.
- \(G(q)\): gravity term.
- \(\tau\): actuator joint torques.
