// Simple numbering for non-book documents
#let equation-numbering = "(1)"
#let callout-numbering = "1"
#let subfloat-numbering(n-super, subfloat-idx) = {
  numbering("1a", n-super, subfloat-idx)
}

// Theorem configuration for theorion
// Simple numbering for non-book documents (no heading inheritance)
#let theorem-inherited-levels = 0

// Theorem numbering format (can be overridden by extensions for appendix support)
// This function returns the numbering pattern to use
#let theorem-numbering(loc) = "1.1"

// Default theorem render function
#let theorem-render(prefix: none, title: "", full-title: auto, body) = {
  if full-title != "" and full-title != auto and full-title != none {
    strong[#full-title.]
    h(0.5em)
  }
  body
}
// Some definitions presupposed by pandoc's typst output.
#let content-to-string(content) = {
  if content.has("text") {
    content.text
  } else if content.has("children") {
    content.children.map(content-to-string).join("")
  } else if content.has("body") {
    content-to-string(content.body)
  } else if content == [ ] {
    " "
  }
}

#let horizontalrule = line(start: (25%,0%), end: (75%,0%))

#let endnote(num, contents) = [
  #stack(dir: ltr, spacing: 3pt, super[#num], contents)
]

#show terms.item: it => block(breakable: false)[
  #text(weight: "bold")[#it.term]
  #block(inset: (left: 1.5em, top: -0.4em))[#it.description]
]

// Some quarto-specific definitions.

#show raw.where(block: true): set block(
    fill: luma(230),
    width: 100%,
    inset: 8pt,
    radius: 2pt
  )

#let block_with_new_content(old_block, new_content) = {
  let fields = old_block.fields()
  let _ = fields.remove("body")
  if fields.at("below", default: none) != none {
    // TODO: this is a hack because below is a "synthesized element"
    // according to the experts in the typst discord...
    fields.below = fields.below.abs
  }
  block.with(..fields)(new_content)
}

#let empty(v) = {
  if type(v) == str {
    // two dollar signs here because we're technically inside
    // a Pandoc template :grimace:
    v.matches(regex("^\\s*$")).at(0, default: none) != none
  } else if type(v) == content {
    if v.at("text", default: none) != none {
      return empty(v.text)
    }
    for child in v.at("children", default: ()) {
      if not empty(child) {
        return false
      }
    }
    return true
  }

}

// Subfloats
// This is a technique that we adapted from https://github.com/tingerrr/subpar/
#let quartosubfloatcounter = counter("quartosubfloatcounter")

#let quarto_super(
  kind: str,
  caption: none,
  label: none,
  supplement: str,
  position: none,
  subcapnumbering: "(a)",
  body,
) = {
  context {
    let figcounter = counter(figure.where(kind: kind))
    let n-super = figcounter.get().first() + 1
    set figure.caption(position: position)
    [#figure(
      kind: kind,
      supplement: supplement,
      caption: caption,
      {
        show figure.where(kind: kind): set figure(numbering: _ => {
          let subfloat-idx = quartosubfloatcounter.get().first() + 1
          subfloat-numbering(n-super, subfloat-idx)
        })
        show figure.where(kind: kind): set figure.caption(position: position)

        show figure: it => {
          let num = numbering(subcapnumbering, n-super, quartosubfloatcounter.get().first() + 1)
          show figure.caption: it => block({
            num.slice(2) // I don't understand why the numbering contains output that it really shouldn't, but this fixes it shrug?
            [ ]
            it.body
          })

          quartosubfloatcounter.step()
          it
          counter(figure.where(kind: it.kind)).update(n => n - 1)
        }

        quartosubfloatcounter.update(0)
        body
      }
    )#label]
  }
}

// callout rendering
// this is a figure show rule because callouts are crossreferenceable
#show figure: it => {
  if type(it.kind) != str {
    return it
  }
  let kind_match = it.kind.matches(regex("^quarto-callout-(.*)")).at(0, default: none)
  if kind_match == none {
    return it
  }
  let kind = kind_match.captures.at(0, default: "other")
  kind = upper(kind.first()) + kind.slice(1)
  // now we pull apart the callout and reassemble it with the crossref name and counter

  // when we cleanup pandoc's emitted code to avoid spaces this will have to change
  let old_callout = it.body.children.at(1).body.children.at(1)
  let old_title_block = old_callout.body.children.at(0)
  let children = old_title_block.body.body.children
  let old_title = if children.len() == 1 {
    children.at(0)  // no icon: title at index 0
  } else {
    children.at(1)  // with icon: title at index 1
  }

  // TODO use custom separator if available
  // Use the figure's counter display which handles chapter-based numbering
  // (when numbering is a function that includes the heading counter)
  let callout_num = it.counter.display(it.numbering)
  let new_title = if empty(old_title) {
    [#kind #callout_num]
  } else {
    [#kind #callout_num: #old_title]
  }

  let new_title_block = block_with_new_content(
    old_title_block,
    block_with_new_content(
      old_title_block.body,
      if children.len() == 1 {
        new_title  // no icon: just the title
      } else {
        children.at(0) + new_title  // with icon: preserve icon block + new title
      }))

  align(left, block_with_new_content(old_callout,
    block(below: 0pt, new_title_block) +
    old_callout.body.children.at(1)))
}

// 2023-10-09: #fa-icon("fa-info") is not working, so we'll eval "#fa-info()" instead
#let callout(body: [], title: "Callout", background_color: rgb("#dddddd"), icon: none, icon_color: black, body_background_color: white) = {
  block(
    breakable: false, 
    fill: background_color, 
    stroke: (paint: icon_color, thickness: 0.5pt, cap: "round"), 
    width: 100%, 
    radius: 2pt,
    block(
      inset: 1pt,
      width: 100%, 
      below: 0pt, 
      block(
        fill: background_color,
        width: 100%,
        inset: 8pt)[#if icon != none [#text(icon_color, weight: 900)[#icon] ]#title]) +
      if(body != []){
        block(
          inset: 1pt, 
          width: 100%, 
          block(fill: body_background_color, width: 100%, inset: 8pt, body))
      }
    )
}


// syntax highlighting functions from skylighting:
/* Function definitions for syntax highlighting generated by skylighting: */
#let EndLine() = raw("\n")
#let Skylighting(fill: none, number: false, start: 1, sourcelines) = {
   let blocks = []
   let lnum = start - 1
   let bgcolor = rgb("#f1f3f5")
   for ln in sourcelines {
     if number {
       lnum = lnum + 1
       blocks = blocks + box(width: if start + sourcelines.len() > 999 { 30pt } else { 24pt }, text(fill: rgb("#aaaaaa"), [ #lnum ]))
     }
     blocks = blocks + ln + EndLine()
   }
   block(fill: bgcolor, width: 100%, inset: 8pt, radius: 2pt, blocks)
}
#let AlertTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let AnnotationTok(s) = text(fill: rgb("#5e5e5e"),raw(s))
#let AttributeTok(s) = text(fill: rgb("#657422"),raw(s))
#let BaseNTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let BuiltInTok(s) = text(fill: rgb("#003b4f"),raw(s))
#let CharTok(s) = text(fill: rgb("#20794d"),raw(s))
#let CommentTok(s) = text(fill: rgb("#5e5e5e"),raw(s))
#let CommentVarTok(s) = text(style: "italic",fill: rgb("#5e5e5e"),raw(s))
#let ConstantTok(s) = text(fill: rgb("#8f5902"),raw(s))
#let ControlFlowTok(s) = text(weight: "bold",fill: rgb("#003b4f"),raw(s))
#let DataTypeTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let DecValTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let DocumentationTok(s) = text(style: "italic",fill: rgb("#5e5e5e"),raw(s))
#let ErrorTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let ExtensionTok(s) = text(fill: rgb("#003b4f"),raw(s))
#let FloatTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let FunctionTok(s) = text(fill: rgb("#4758ab"),raw(s))
#let ImportTok(s) = text(fill: rgb("#00769e"),raw(s))
#let InformationTok(s) = text(fill: rgb("#5e5e5e"),raw(s))
#let KeywordTok(s) = text(weight: "bold",fill: rgb("#003b4f"),raw(s))
#let NormalTok(s) = text(fill: rgb("#003b4f"),raw(s))
#let OperatorTok(s) = text(fill: rgb("#5e5e5e"),raw(s))
#let OtherTok(s) = text(fill: rgb("#003b4f"),raw(s))
#let PreprocessorTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let RegionMarkerTok(s) = text(fill: rgb("#003b4f"),raw(s))
#let SpecialCharTok(s) = text(fill: rgb("#5e5e5e"),raw(s))
#let SpecialStringTok(s) = text(fill: rgb("#20794d"),raw(s))
#let StringTok(s) = text(fill: rgb("#20794d"),raw(s))
#let VariableTok(s) = text(fill: rgb("#111111"),raw(s))
#let VerbatimStringTok(s) = text(fill: rgb("#20794d"),raw(s))
#let WarningTok(s) = text(style: "italic",fill: rgb("#5e5e5e"),raw(s))



#let article(
  title: none,
  subtitle: none,
  authors: none,
  keywords: (),
  date: none,
  abstract-title: none,
  abstract: none,
  thanks: none,
  cols: 1,
  lang: "en",
  region: "US",
  font: none,
  fontsize: 11pt,
  title-size: 1.5em,
  subtitle-size: 1.25em,
  heading-family: none,
  heading-weight: "bold",
  heading-style: "normal",
  heading-color: black,
  heading-line-height: 0.65em,
  mathfont: none,
  codefont: none,
  linestretch: 1,
  sectionnumbering: none,
  linkcolor: none,
  citecolor: none,
  filecolor: none,
  toc: false,
  toc_title: none,
  toc_depth: none,
  toc_indent: 1.5em,
  doc,
) = {
  // Set document metadata for PDF accessibility
  set document(title: title, keywords: keywords)
  set document(
    author: authors.map(author => content-to-string(author.name)).join(", ", last: " & "),
  ) if authors != none and authors != ()
  set par(
    justify: true,
    leading: linestretch * 0.65em
  )
  set text(lang: lang,
           region: region,
           size: fontsize)
  set text(font: font) if font != none
  show math.equation: set text(font: mathfont) if mathfont != none
  show raw: set text(font: codefont) if codefont != none

  set heading(numbering: sectionnumbering)

  show link: set text(fill: rgb(content-to-string(linkcolor))) if linkcolor != none
  show ref: set text(fill: rgb(content-to-string(citecolor))) if citecolor != none
  show link: this => {
    if filecolor != none and type(this.dest) == label {
      text(this, fill: rgb(content-to-string(filecolor)))
    } else {
      text(this)
    }
   }

  let has-title-block = title != none or (authors != none and authors != ()) or date != none or abstract != none
  if has-title-block {
    place(
      top,
      float: true,
      scope: "parent",
      clearance: 4mm,
      block(below: 1em, width: 100%)[

        #if title != none {
          align(center, block(inset: 2em)[
            #set par(leading: heading-line-height) if heading-line-height != none
            #set text(font: heading-family) if heading-family != none
            #set text(weight: heading-weight)
            #set text(style: heading-style) if heading-style != "normal"
            #set text(fill: heading-color) if heading-color != black

            #text(size: title-size)[#title #if thanks != none {
              footnote(thanks, numbering: "*")
              counter(footnote).update(n => n - 1)
            }]
            #(if subtitle != none {
              parbreak()
              text(size: subtitle-size)[#subtitle]
            })
          ])
        }

        #if authors != none and authors != () {
          let count = authors.len()
          let ncols = calc.min(count, 3)
          grid(
            columns: (1fr,) * ncols,
            row-gutter: 1.5em,
            ..authors.map(author =>
                align(center)[
                  #author.name \
                  #author.affiliation \
                  #author.email
                ]
            )
          )
        }

        #if date != none {
          align(center)[#block(inset: 1em)[
            #date
          ]]
        }

        #if abstract != none {
          block(inset: 2em)[
          #text(weight: "semibold")[#abstract-title] #h(1em) #abstract
          ]
        }
      ]
    )
  }

  if toc {
    let title = if toc_title == none {
      auto
    } else {
      toc_title
    }
    block(above: 0em, below: 2em)[
    #outline(
      title: toc_title,
      depth: toc_depth,
      indent: toc_indent
    );
    ]
  }

  doc
}

#set table(
  inset: 6pt,
  stroke: none
)
#set par(justify: false, leading: 0.7em)
#set heading(outlined: true)
#show table: set text(size: 8.5pt)
#let brand-color = (:)
#let brand-color-background = (:)
#let brand-logo = (:)

#set page(
  paper: "a4",
  margin: (x: 19mm,y: 18mm,),
  numbering: "1",
  columns: 1,
)

#show: doc => article(
  title: [Tracking Accuracy and Robustness of a Planar Two-DOF Robot Arm],
  subtitle: [A Reproducible Comparison of PID, Gravity Compensation, and Computed Torque Control],
  date: [2026-09-17],
  lang: "en",
  font: ("Arial",),
  fontsize: 10pt,
  heading-family: ("Arial",),
  sectionnumbering: "1.1.a",
  toc_title: [Table of contents],
  toc_depth: 3,
  doc,
)

#heading(level: 2, numbering: none)[Abstract]
<abstract>
This study compares independent-joint PID, PID with gravity compensation, and computed torque control (CTC) on a robot moving in a vertical plane under a shared trajectory, sampling interval, and torque limit. Gains are selected on a separate training trajectory and frozen before 42 deterministic evaluation runs covering nominal conditions, unknown endpoint payloads, controller-model parameter errors, and external endpoint force. Nominal joint RMSE values are 1.115037 / 0.152634 / 0.004992 degrees, and formal disturbance recovery delays are 1.555 / 0.087 / 0.263 seconds, in the same controller order. CTC achieves the smallest nominal tracking error, but its advantage does not generalize to all payload, model mismatch, or disturbance cases. Saturation and degraded runs are retained. Control effort, absolute mechanical work, and baseline-relative disturbance diagnostics are explicitly distinguished. Tables, numerical statements, and figures are assembled automatically from accepted results, without retuning the controllers.

#strong[Keywords:] two-DOF robot arm; computed torque control; gravity compensation; model mismatch; reproducible simulation.

#pagebreak()
= Introduction
<introduction>
Robot models reduce the dynamic errors that feedback must compensate, but introduce dependence on model accuracy. This project compares three controllers on the same arm and trajectory under nominal conditions, unknown payloads, controller-model errors, and external force.

The charter predicted that CTC would track best nominally, degrade fastest with unknown payload, and lose its advantage over PID as model error grows; gravity-compensated PID would recover fastest after force removal. Predictions are tested, not used to select results. Robustness here describes finite predefined scenarios, not a universal stability proof.

The theoretical basis is #link("https://modernrobotics.northwestern.edu/nu-gm-book-resource/11-4-motion-control-with-torque-or-force-inputs-part-3-of-3/")[Modern Robotics torque control]. The project's implementation defines its particular PD-type CTC, PID integral update, sampling, and saturation; the teaching material does not establish these experimental results.

= Model
<model>
== Coordinates and Kinematics
<coordinates-and-kinematics>
The arm moves in a vertical plane. Positive $x$ points horizontally right and positive $y$ vertically upward. The angle $q_1$ is measured counterclockwise from the horizontal axis; $q_2$ is the angle of the second link relative to the first. Internal calculations use SI units and radians; plots may display degrees.

$ x = l_1 cos q_1 + l_2 cos\(q_1 + q_2\)\,#h(2em) y = l_1 sin q_1 + l_2 sin\(q_1 + q_2\). $

End-effector velocity satisfies $dot(p) = J\(q\)dot(q)$. A force in the base frame produces joint torque $tau_(upright(e x t)) =\(J\(q\)^T\)F$. The force mapping uses the actual configuration, not the reference configuration.

== Rigid-Body Dynamics
<rigid-body-dynamics>
$ M\(q\)dot.double(q) + c\(q\,dot(q)\)+ G\(q\)= tau + tau_(upright(e x t)) . $

Let $q_12 = q_1 + q_2$. Without payload, the independent mass-matrix entries are

$ M_11 & = I_1 + I_2 + m_1 l_(c 1)^2 + m_2\(l_1^2 + l_(c 2)^2 + 2 l_1 l_(c 2) cos q_2\)\,\
M_12 & = M_21 = I_2 + m_2\(l_(c 2)^2 + l_1 l_(c 2) cos q_2\)\,\
M_22 & = I_2 + m_2 l_(c 2)^2 . $

With $h = m_2 l_1 l_(c 2) sin q_2$,

$ c = mat(delim: "[", - h\(2 dot(q)_1 dot(q)_2 + dot(q)_2^2\); h dot(q)_1^2)\,#h(2em) G = g mat(delim: "[", \(m_1 l_(c 1) + m_2 l_1\)cos q_1 + m_2 l_(c 2) cos q_12; m_2 l_(c 2) cos q_12) . $

The endpoint payload is a point mass $m_p$. It adds $Delta M = m_p\(J^T\)J$ and corresponding Coriolis/centrifugal and gravity terms. Specifically, $h$ gains $m_p l_1 l_2 sin q_2$, and $G$ gains $m_p g\[l_1 cos q_1 + l_2 cos q_12\,med l_2 cos q_12\]^T$. Payload therefore changes inertia, motion coupling, and gravity, rather than merely adding constant torque.

#figure([
#table(
  columns: 3,
  align: (auto,auto,auto,),
  table.header([Parameter], [Value], [Unit],),
  table.hline(),
  [l1], [0.5], [m],
  [l2], [0.4], [m],
  [lc1], [0.25], [m],
  [lc2], [0.2], [m],
  [m1], [2], [kg],
  [m2], [1.5], [kg],
  [I1], [0.041666667], [kg·m²],
  [I2], [0.02], [kg·m²],
  [g], [9.81], [m/s²],
)
], caption: figure.caption(
position: top, 
[
Nominal parameters read from the accepted nominal YAML.
]), 
kind: "quarto-float-tbl", 
supplement: "Table", 
)
<tbl-parameters>


#pagebreak()
= Trajectory
<trajectory>
Each segment uses rest-to-rest quintic time scaling. With normalized time $u =\(t - t_0\)\/T$,

$ s\(u\)= 10 u^3 - 15 u^4 + 6 u^5\,#h(2em) q_d = q_a +\(q_b - q_a\)s\(u\). $

Velocity and acceleration follow from analytic derivatives and are zero at every waypoint. The training trajectory is \[-35°, -45°\] → \[50°, 60°\] over 4.0 s, used only for gain selection. The held-out test trajectory is listed below. All four experiment families use identical test trajectories and initial states.

#figure([
#table(
  columns: 3,
  align: (auto,auto,auto,),
  table.header([Time (s)], [q₁ (°)], [q₂ (°)],),
  table.hline(),
  [0.0], [20], [-35],
  [2.0], [-40], [25],
  [4.0], [55], [45],
  [6.0], [5], [-50],
  [8.0], [-30], [15],
)
], caption: figure.caption(
position: top, 
[
Held-out test waypoints.
]), 
kind: "quarto-float-tbl", 
supplement: "Table", 
)
<tbl-waypoints>


The initial position equals the first waypoint; initial velocity and PID integral error are zero. Error statistics include the initial transient, with no warm-up exclusion or removal of unfavorable intervals.

= Controllers
<controllers>
Let $e = q_d - q$ and $dot(e) = dot(q)_d - dot(q)$. All gain matrices are diagonal.

#strong[Independent-joint PID:] $tau_(upright(r e q)) = K_p e + K_d dot(e) + K_i z$. Conditional integration freezes a joint's integral when that joint is saturated and $tau_i e_i > 0$\; otherwise, it advances the integral using the current error. This prevents accumulation that would worsen saturation.

#strong[PID with gravity compensation:] $tau_(upright(r e q)) = K_p e + K_d dot(e) + K_i z + hat(G)\(q\)$. Compensation uses the controller's internal model. Plant and controller parameters are stored separately, allowing independent model errors.

#strong[CTC:]

$ tau_(upright(r e q)) = hat(M)\(q\)\(dot.double(q)_d + K_d dot(e) + K_p e\)+ hat(c)\(q\,dot(q)\)+ hat(G)\(q\). $

This CTC has no integral term. With an exact model, no saturation, and ideal continuous control, the error satisfies

$ dot.double(e) + K_d dot(e) + K_p e = - M\(q\)^(- 1)tau_(upright(e x t)) . $

Unknown external force still drives error: nominal model compensation does not compensate unknown force. The experiments use sampled control, so this ideal continuous equation is not an exact identity of the discrete simulation.

All requested torques pass through a common actuator limit of ±20.0 N·m per joint. PID gains $K_p\,K_d\,K_i$ have units N·m/rad, N·m·s/rad, and N·m/(rad·s), respectively. CTC gains $K_p\,K_d$ have units s$""^(- 2)$ and s$""^(- 1)$, so numerical gain magnitudes alone cannot compare control strength.

#figure([
#table(
  columns: 4,
  align: (auto,auto,auto,auto,),
  table.header([Controller], [Kp], [Ki], [Kd],),
  table.hline(),
  [PID], [\(270.65, 102.72)], [\(95.432, 64.325)], [\(16.835, 33.577)],
  [PID+G], [\(288.13, 193.82)], [\(16.906, 71.103)], [\(43.649, 27.903)],
  [CTC], [\(106.34, 142.6)], [N/A], [\(24.42, 22.309)],
)
], caption: figure.caption(
position: top, 
[
Frozen gains, with entries ordered by joint. Display rounding does not change simulation parameters.
]), 
kind: "quarto-float-tbl", 
supplement: "Table", 
)
<tbl-gains>


#pagebreak()
= Methodology
<methodology>
== Tuning and Fairness
<tuning-and-fairness>
Each controller uses 300 candidates, totaling 900, with seed 20260905. PID variants search joint gains directly; CTC is parameterized by natural frequency and damping ratio. All share the training trajectory, initial state, time step, torque limits, and objective:

$ S = 0.7 E_n + 0.2 U_n + 0.1 r_(upright(s a t)) . $

$E_n$ is the overall RMSE after each joint's error is normalized by its training-trajectory angular span; $U_n = integral sum_i tau_i^2 d t\/\(T sum_i tau_(max\,i)^2\)$. Failed candidates are excluded; ties are resolved by control effort and then candidate ID. Screening rules and all candidates are retained in the frozen tuning file. This controls search budget, but parameterization and search ranges may still affect rankings; global optimality is not established.

== Scenarios and Integration
<scenarios-and-integration>
#figure([
#table(
  columns: (33.33%, 33.33%, 33.33%),
  align: (auto,auto,auto,),
  table.header([Scenario], [Condition], [Runs],),
  table.hline(),
  [Nominal], [Identical plant and controller models], [3],
  [Payload], [0.0, 0.25, 0.5, 0.75, 1.0 kg; payload added to the plant only], [15],
  [Model uncertainty], [-30%, -20%, -10%, 0%, 10%, 20%, 30%], [21],
  [Disturbance], [F=\[10.0, 0.0\] N，\[4.5, 4.7) s], [3],
)
], caption: figure.caption(
position: top, 
[
Fixed scenario grid. Model errors change only controller parameters $hat(m)_2\,hat(I)_2$\; the plant remains nominal.
]), 
kind: "quarto-float-tbl", 
supplement: "Table", 
)
<tbl-scenarios>


The fixed RK4 step and control period are both 0.001 s. Motor torque remains constant within each control interval. In disturbance experiments, constant base-frame force is mapped through $\(J\(q\)^T\)F$ at the actual $q$ of every RK4 substep. Each run contains 8001 state samples; the endpoint is recorded without further integration. Control effort includes motor torque only, not external torque.

This reporting stage reads accepted histories without repeating simulations. Existing automated tests cover the model, simulator, controllers, and Stage 21 analysis. They verify implementation and do not replace independent physical experiments.

== Metrics and Sources
<metrics-and-sources>
$ E_q = sqrt(frac(1, 2 N) sum_(k = 1)^N sum_(i = 1)^2 e_(k\,i)^2)\,quad E_p = sqrt(1 / N sum_(k = 1)^N parallel p_d - p parallel_2^2) . $

Peak end-effector error is the maximum Euclidean distance in the specified window. Control effort $U = integral sum_i tau_i^2 d t$, in (N·m)$""^2$·s, #strong[is not energy]. Absolute total mechanical work $W = integral\|sum_i tau_i dot(q)_i\|d t$, in J, is not electrical consumption either. Integral metrics use actual applied torque and interval-start samples. Saturation fraction measures the duration of intervals with either joint saturated.

Formal recovery is measured from force removal: error must remain at or below 10.0 mm for at least 0.5 s. The reported delay is the start of the first qualifying window. Recovery not confirmed within the record remains unconfirmed and is not reported as zero seconds. Nominal-relative deviations in the figures are diagnostic and do not replace this metric.

Stage 21's #NormalTok("summary.csv"); and figures supply the report's numerical results. Their manifest hashes are checked before assembly; experiment parameters come from the same source YAML files. All scenarios are retained. These deterministic runs provide no independent random replicates, so no statistical error bars, confidence intervals, or significance tests are constructed.

#pagebreak()
= Results
<results>
== Nominal Tracking
<nominal-tracking>
#figure([
#table(
  columns: 5,
  align: (auto,auto,auto,auto,auto,),
  table.header([Controller], [RMSE (°)], [EE RMSE (mm)], [Effort], [Work (J)],),
  table.hline(),
  [PID], [1.115037], [25.3661], [1440.970], [54.452],
  [PID+G], [0.152634], [3.5193], [1444.343], [53.683],
  [CTC], [0.004992], [0.0372], [1446.349], [53.497],
)
], caption: figure.caption(
position: top, 
[
Nominal accuracy and control input. RMSE aggregates both joints; work integrates absolute total power.
]), 
kind: "quarto-float-tbl", 
supplement: "Table", 
)
<tbl-nominal>


The positions in #ref(<fig-track>, supplement: [Figure]) closely follow the reference, while #ref(<fig-error>, supplement: [Figure]) reveals distinct tracking errors. Nominal RMSE values are 1.115037 / 0.152634 / 0.004992 degrees for PID, PID with gravity compensation, and CTC, respectively. CTC has the smallest error and gravity-compensated PID is intermediate. Control efforts remain similar, so improved accuracy should not be described as a proportional reduction in energy consumption.

#figure([
#box(image("figures/01_nominal_tracking.png", width: 100.0%))
], caption: figure.caption(
position: bottom, 
[
Nominal joint positions and reference trajectories; all controllers share the reference and initial state.
]), 
kind: "quarto-float-fig", 
supplement: "Figure", 
)
<fig-track>


#figure([
#box(image("figures/02_nominal_error.png", width: 100.0%))
], caption: figure.caption(
position: bottom, 
[
Nominal joint errors, retaining initial transients and every sampling interval.
]), 
kind: "quarto-float-fig", 
supplement: "Figure", 
)
<fig-error>


#pagebreak()
== Nominal Control Input and Combined Metrics
<nominal-control-input-and-combined-metrics>
#ref(<fig-torque>, supplement: [Figure]) shows actual motor torques and shared limits; each controller has saturation fraction 0.000 / 0.000 / 0.000%. #ref(<fig-metrics>, supplement: [Figure]) presents accuracy, effort, and mechanical work together. Small error-metric bars retain numerical labels rather than being described as exactly zero.

#figure([
#box(image("figures/03_nominal_torque.png", width: 100.0%))
], caption: figure.caption(
position: bottom, 
[
Actual nominal motor torque; dashed lines indicate shared actuator limits.
]), 
kind: "quarto-float-fig", 
supplement: "Figure", 
)
<fig-torque>


#figure([
#box(image("figures/04_nominal_metrics.png", width: 90.0%))
], caption: figure.caption(
position: bottom, 
[
Nominal accuracy, control effort, and absolute total mechanical work, each in its own units.
]), 
kind: "quarto-float-fig", 
supplement: "Figure", 
)
<fig-metrics>


#pagebreak()
== Unknown Endpoint Payload
<unknown-endpoint-payload>
#ref(<fig-payload>, supplement: [Figure]) includes the full mass grid. At 0.25 kg, overall joint RMSE values are 1.381 / 0.339 / 3.967 degrees. At the maximum 1.0 kg payload, they reach 32.491 / 32.553 / 40.108 degrees, with saturation fractions 95.513 / 92.375 / 64.312%. These degraded runs remain in the analysis.

#figure([
#box(image("figures/05_payload.png", width: 100.0%))
], caption: figure.caption(
position: bottom, 
[
Payload effects on overall joint error, control effort, and saturation fraction.
]), 
kind: "quarto-float-fig", 
supplement: "Figure", 
)
<fig-payload>


#figure([
#table(
  columns: 4,
  align: (auto,auto,auto,auto,),
  table.header([Payload (kg)], [PID], [PID+G], [CTC],),
  table.hline(),
  [0.0], [1.115037], [0.152634], [0.004992],
  [0.25], [1.380694], [0.338827], [3.967051],
  [0.5], [3.851948], [2.936610], [15.061124],
  [0.75], [19.789138], [18.388365], [29.155920],
  [1.0], [32.490911], [32.552774], [40.108152],
)
], caption: figure.caption(
position: top, 
[
All payload joint RMSE values in degrees; controller order is fixed.
]), 
kind: "quarto-float-tbl", 
supplement: "Table", 
)
<tbl-payload>


At maximum payload, RMSE ratios relative to each controller's own nominal result are 29.139 / 213.273 / 8034.353. CTC's very small nominal denominator magnifies relative deterioration; absolute errors are therefore also reported. Joint and end-effector errors need not yield the same ranking, because large angular deviations change the geometric correspondence.

== Controller-Model Parameter Error
<controller-model-parameter-error>
In #ref(<fig-model>, supplement: [Figure]), the plant is unchanged and both selected controller parameters are multiplied by $1 + delta$. PID uses no internal dynamics model, so its RMSE remains 1.115037 degrees throughout the grid. CTC RMSE at -30% and +30% error is 2.828458 and 1.566751 degrees, respectively, versus 0.004992 degrees at zero error. Sensitivity is asymmetric.

#figure([
#box(image("figures/06_model_uncertainty.png", width: 100.0%))
], caption: figure.caption(
position: bottom, 
[
Shared relative error in controller-model mass and inertia; no controller saturates in this experiment.
]), 
kind: "quarto-float-fig", 
supplement: "Figure", 
)
<fig-model>


#pagebreak()
== External Endpoint Force
<external-endpoint-force>
The base-frame force is \[10.0, 0.0\] N during \[4.5, 4.7) s. The left panel of #ref(<fig-response>, supplement: [Figure]) shows absolute reference error; the right shows additional deviation from the same controller's nominal trajectory. Their difference illustrates how baseline tracking error affects recovery time.

#figure([
#box(image("figures/07_disturbance_response.png", width: 100.0%))
], caption: figure.caption(
position: bottom, 
[
Force response: formal tracking error on the left and diagnostic nominal-relative deviation on the right.
]), 
kind: "quarto-float-fig", 
supplement: "Figure", 
)
<fig-response>


#figure([
#table(
  columns: (20%, 20%, 20%, 20%, 20%),
  align: (auto,auto,auto,auto,auto,),
  table.header([Controller], [Recovery (s)], [Full-run peak (mm)], [Post-disturbance peak (mm)], [Saturation %],),
  table.hline(),
  [PID], [1.555], [54.107], [27.644], [0.000],
  [PID+G], [0.087], [17.564], [17.564], [0.000],
  [CTC], [0.263], [102.448], [102.448], [0.000],
)
], caption: figure.caption(
position: top, 
[
Disturbance recovery and peaks. Full-run and post-disturbance peaks are reported separately.
]), 
kind: "quarto-float-tbl", 
supplement: "Table", 
)
<tbl-disturbance>


All three controllers recover within the observation window, with formal delays of 1.555 / 0.087 / 0.263 s. PID with gravity compensation is fastest, followed by CTC and PID. Post-disturbance endpoint peaks are 27.644 / 17.564 / 102.448 mm. Fast recovery and small peak error must therefore be reported separately.

#figure([
#box(image("figures/08_disturbance_metrics.png", width: 100.0%))
], caption: figure.caption(
position: bottom, 
[
Formal recovery delay from pulse removal and peak error between disturbance onset and trajectory completion.
]), 
kind: "quarto-float-fig", 
supplement: "Figure", 
)
<fig-recovery>


#pagebreak()
= Discussion
<discussion>
== Responses to the Charter Predictions
<responses-to-the-charter-predictions>
#strong[The nominal-accuracy prediction is supported by these data.] CTC has the smallest overall joint RMSE with an accurate model. However, all controllers were tuned separately, so the full benefit cannot be attributed to adding a single compensation term. Structure and tuning jointly determine the observed differences.

#strong[The unknown-payload prediction requires a specified metric.] CTC shows the strongest increase in joint RMSE relative to its own nominal baseline and larger joint RMSE at the tested nonzero payloads. End-effector rankings can differ because of geometric mapping and large angular deviations; CTC is not necessarily worst on every payload metric. Larger payloads also cause saturation, so mismatch and actuator capacity cannot be isolated in these runs.

#strong[The model-error prediction receives conditional support.] CTC is best near zero error; its advantage decreases in either direction and it may underperform model-independent PID at larger mismatch. Positive and negative errors are asymmetric and should not be fitted by a single line in absolute error. Gravity-compensated PID degrades less across this grid, without guaranteeing the same behavior for other trajectories or parameter errors.

#strong[The recovery prediction is supported by the formal metric.] Gravity-compensated PID meets the threshold first. PID's longer formal recovery includes baseline tracking error, which the diagnostic panel helps distinguish. External force still drives CTC error; high nominal accuracy does not guarantee smaller disturbance peaks or faster recovery.

== Interpretation Boundaries
<interpretation-boundaries>
A best-controller claim must specify operating conditions and metrics. Nominal accuracy, parameter sensitivity, actuator saturation, disturbance peaks, and recovery time are different objectives. Squared-torque effort is a tuning penalty, not electrical energy. Mechanical work also excludes motor and drive losses and regenerative-braking efficiency. These data therefore do not support energy-saving claims.

= Limitations
<limitations>
The study covers one fixed robot, training and held-out trajectories, finite payload and error grids, and one force direction and pulse interval. It excludes friction, backlash, delay, flexibility, and sensor noise; controllers receive true joint states. The finite candidate budget does not establish global optimality, and parameterizations differ. Fixed-step integration and sampled holds introduce discretization effects. All findings are simulation results, without hardware validation or universal guarantees for untested conditions or closed-loop stability.

Future work could add stochastic repeats, noise, multiple force directions, other trajectories, and matched-gain ablations. These extensions are not used to retune the current controllers. Failed and degraded conditions remain visible, without selection based on the expected conclusion.

= Conclusion
<conclusion>
With frozen gains and shared test conditions, CTC achieves the highest nominal tracking accuracy. Unknown payload, model error, and force disturbances change the relationship among controllers. Gravity-compensated PID recovers fastest under the formal disturbance criterion. These data support no single winner across every condition and metric. Traceable sources, automatic numerical assembly, fixed figures, and HTML/PDF outputs from one source make the results reviewable.

#pagebreak()
= Reproducibility and Sources
<reproducibility-and-sources>
#NormalTok("stage22/build_report.py"); assembles the report from fixed Stage 21 outputs and original configurations, then Quarto renders HTML and Typst PDF from the same source. HTML embeds resources and uses MathML; the English PDF uses Arial. The rendering workflow follows the #link("https://quarto.org/docs/output-formats/typst.html")[official Quarto Typst documentation] and needs no separate LaTeX installation. Raw results are not modified, and failed builds are not marked as accepted.

From the project root, with the project environment activated:

#Skylighting(([#NormalTok("python stage22");#OperatorTok("/");#NormalTok("build_report");#OperatorTok(".");#FunctionTok("py");#NormalTok(" ");#OperatorTok("--");#NormalTok("output stage22");#OperatorTok("/");#NormalTok("rebuilt_report");],));
Existing output directories are protected. Use #NormalTok("--output"); to select a new directory. The package includes the full CSV, eight source figures, generated Quarto source, HTML, PDF, and a build manifest with input, program, and output hashes. Raw NPZ/YAML paths in the CSV are relative to this project root. Tables display rounded values; the CSV retains full precision.

#figure([
#table(
  columns: 2,
  align: (auto,auto,),
  table.header([Scenario], [Run directory under results/],),
  table.hline(),
  [nominal], [#NormalTok("20260907T024619_815442Z");],
  [payload], [#NormalTok("20260911T014147_244577Z");],
  [model\_uncertainty], [#NormalTok("20260911T025328_299278Z");],
  [disturbance], [#NormalTok("20260913T114926_385587Z");],
)
], caption: figure.caption(
position: top, 
[
Fixed run directories used by this report.
]), 
kind: "quarto-float-tbl", 
supplement: "Table", 
)
<tbl-sources>


#strong[References and Project Evidence]

- Modern Robotics, Chapter 11.4: computed torque and dynamic model compensation; linked in the introduction.
- Official Quarto Typst documentation: PDF rendering and font configuration; linked above.
- #NormalTok("RESEARCH_CHARTER.md");: predefined research questions and four predictions.
- Frozen #NormalTok("results/tuning_search.json");: all candidates, objective, seed, and final selections.
- Stage 21 summary, figures, and manifest: experimental results and their source provenance.

#pagebreak()
= Full Results
<full-results>
These tables retain all 42 runs. Joint RMSE is in degrees; endpoint RMSE and full-run peak are in mm; saturation is in %. The accompanying #NormalTok("summary.csv"); retains full fields for effort, absolute mechanical work, recovery status, normalized results, and source paths.

== nominal
<nominal>
#table(
  columns: 6,
  align: (auto,auto,auto,auto,auto,auto,),
  table.header([Parameter], [Controller], [Joint RMSE], [EE RMSE], [Full-run peak], [Saturation %],),
  table.hline(),
  [---], [PID], [1.115037], [25.366], [54.107], [0.000],
  [---], [PID+G], [0.152634], [3.519], [7.221], [0.000],
  [---], [CTC], [0.004992], [0.037], [0.101], [0.000],
)
== payload
<payload>
#table(
  columns: 6,
  align: (auto,auto,auto,auto,auto,auto,),
  table.header([Parameter], [Controller], [Joint RMSE], [EE RMSE], [Full-run peak], [Saturation %],),
  table.hline(),
  [0.0], [PID], [1.115037], [25.366], [54.107], [0.000],
  [0.0], [PID+G], [0.152634], [3.519], [7.221], [0.000],
  [0.0], [CTC], [0.004992], [0.037], [0.101], [0.000],
  [0.25], [PID], [1.380694], [31.104], [67.972], [1.275],
  [0.25], [PID+G], [0.338827], [7.785], [15.167], [0.000],
  [0.25], [CTC], [3.967051], [28.539], [41.753], [0.000],
  [0.5], [PID], [3.851948], [81.910], [249.523], [32.625],
  [0.5], [PID+G], [2.936610], [60.548], [213.262], [25.275],
  [0.5], [CTC], [15.061124], [68.595], [163.053], [24.375],
  [0.75], [PID], [19.789138], [401.421], [780.065], [83.188],
  [0.75], [PID+G], [18.388365], [371.861], [825.579], [90.112],
  [0.75], [CTC], [29.155920], [153.646], [394.210], [53.688],
  [1.0], [PID], [32.490911], [642.289], [1246.316], [95.513],
  [1.0], [PID+G], [32.552774], [635.600], [1229.850], [92.375],
  [1.0], [CTC], [40.108152], [264.565], [586.778], [64.312],
)
== model\_uncertainty
<model_uncertainty>
#table(
  columns: 6,
  align: (auto,auto,auto,auto,auto,auto,),
  table.header([Parameter], [Controller], [Joint RMSE], [EE RMSE], [Full-run peak], [Saturation %],),
  table.hline(),
  [-0.3], [PID], [1.115037], [25.366], [54.107], [0.000],
  [-0.3], [PID+G], [0.372387], [8.519], [15.129], [0.000],
  [-0.3], [CTC], [2.828458], [38.008], [52.026], [0.000],
  [-0.2], [PID], [1.115037], [25.366], [54.107], [0.000],
  [-0.2], [PID+G], [0.280691], [6.442], [12.492], [0.000],
  [-0.2], [CTC], [1.657619], [22.424], [30.459], [0.000],
  [-0.1], [PID], [1.115037], [25.366], [54.107], [0.000],
  [-0.1], [PID+G], [0.200772], [4.629], [9.857], [0.000],
  [-0.1], [CTC], [0.739656], [10.056], [13.572], [0.000],
  [0.0], [PID], [1.115037], [25.366], [54.107], [0.000],
  [0.0], [PID+G], [0.152634], [3.519], [7.221], [0.000],
  [0.0], [CTC], [0.004992], [0.037], [0.101], [0.000],
  [0.1], [PID], [1.115037], [25.366], [54.107], [0.000],
  [0.1], [PID+G], [0.166760], [3.797], [7.584], [0.000],
  [0.1], [CTC], [0.611066], [8.335], [11.144], [0.000],
  [0.2], [PID], [1.115037], [25.366], [54.107], [0.000],
  [0.2], [PID+G], [0.232168], [5.248], [10.190], [0.000],
  [0.2], [CTC], [1.125612], [15.360], [20.461], [0.000],
  [0.3], [PID], [1.115037], [25.366], [54.107], [0.000],
  [0.3], [PID+G], [0.318798], [7.198], [13.659], [0.000],
  [0.3], [CTC], [1.566751], [21.361], [28.369], [0.000],
)
== disturbance
<disturbance>
#table(
  columns: 6,
  align: (auto,auto,auto,auto,auto,auto,),
  table.header([Parameter], [Controller], [Joint RMSE], [EE RMSE], [Full-run peak], [Saturation %],),
  table.hline(),
  [---], [PID], [1.103720], [25.197], [54.107], [0.000],
  [---], [PID+G], [0.176402], [3.997], [17.564], [0.000],
  [---], [CTC], [2.237485], [15.139], [102.448], [0.000],
)



