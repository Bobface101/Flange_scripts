## ASME Flanges
import math
import csv
import os
from fractions import Fraction

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'ASME_data.csv')
output_file = os.path.join(script_dir, 'commands.scr')
scr_lines = []

def bolt_spec(diameter):
    soft_conversion = {"0.5":"M14","0.625":"M16", "0.75":"M20", "0.875":"M24"}
    return (Fraction(str(diameter)), soft_conversion[diameter])

def fmt(pt):
    """format point as an AutoCAD coordinate string."""
    x, y = pt
    return f"{x:g},{y:g}"

def lengthof(p1, p2):
     x1,y1 = p1
     x2,y2 = p2
     return ((x1-x2)**2 + (y1-y2)**2)**0.5

def fillet_arc_mid(vertex, prev_pt, next_pt, radius):
    """Point on the fillet arc body (not the ghost vertex)."""
    a1 = math.atan2(prev_pt[1]-vertex[1], prev_pt[0]-vertex[0])
    a2 = math.atan2(next_pt[1]-vertex[1], next_pt[0]-vertex[0])
    bisect = (a1 + a2) / 2
    half = abs(a1 - a2) / 2
    offset = radius / math.sin(half) - radius if half > 0.01 else 0.1
    return (vertex[0] + offset * math.cos(bisect),
            vertex[1] + offset * math.sin(bisect))

def midpoint(*points):   
    num_points = len(points)
    x_avg = sum(p[0] for p in points) / num_points
    y_avg = sum(p[1] for p in points) / num_points
    return (x_avg, y_avg)

def conjugate(pt): # reflects point in mirror line of FLANGE, not x-axis
    x, y = pt
    return(x, 2*sy-y)

def symmetric_diameter_dim(extent, offset, point_on_face):
        scr_lines.append("DIMLINEAR")
        scr_lines.append(fmt(extent))
        scr_lines.append(fmt(conjugate(extent))) # symmetrical diameter 
        scr_lines.append("T") # text edit 
        scr_lines.append("%%c<>") 
        scr_lines.append(fmt(((point_on_face[0]+offset),(sy)))) 

def linear_dim(p1, p2, placement, text_override=None):
    scr_lines.append("DIMLINEAR")
    scr_lines.append(fmt(p1))
    scr_lines.append(fmt(p2)) 

    # Only inject the "T" command if a string was actually passed in
    if text_override is not None:
        scr_lines.append("T") 
        scr_lines.append(text_override) 

    scr_lines.append(fmt(placement))

def line(*points):
    scr_lines.append("LINE")
    for p in points: 
        scr_lines.append(fmt(p))
    scr_lines.append(fmt(points[0]))
    scr_lines.append("")


def draw_roughness_symbol(startpos, sidelength):
        h = sidelength * (3**0.5 / 2)
        p_left = (startpos[0] - sidelength / 2, startpos[1] + h)
        p_right = (startpos[0] + sidelength / 2, startpos[1] + h)
        p_ext = (startpos[0] + sidelength, startpos[1] + 2 * h)

        scr_lines.append("LINE")
        scr_lines.append(fmt(p_left))
        scr_lines.append(fmt(startpos))
        scr_lines.append(fmt(p_ext))
        scr_lines.append("")

        scr_lines.append("LINE")
        scr_lines.append(fmt(p_left))
        scr_lines.append(fmt(p_right))
        scr_lines.append("")

def draw_check_mark(startpos, sidelength):
    x, y = startpos
    s = sidelength

    def draw_arc(p1, p2, p3):
        scr_lines.append("ARC")
        scr_lines.append(fmt(p1))
        scr_lines.append(fmt(p2))
        scr_lines.append(fmt(p3))

    scr_lines.append("LINE")
    scr_lines.append(fmt((x - 0.45 * s, y + 0.45 * s)))  
    scr_lines.append(fmt((x - 0.15 * s, y + 0.15 * s)))  
    scr_lines.append(fmt((x + 0.60 * s, y + 0.90 * s)))  
    scr_lines.append("")

    draw_arc((x - 0.7 * s, y + s), (x - 0.95 * s, y + 0.5 * s), (x - 0.7 * s, y))
    draw_arc((x + 0.7 * s, y + s), (x + 0.95 * s, y + 0.5 * s), (x + 0.7 * s, y))

def add_sysvar(name, value):
    """Add a system variable setting to the script.
      VARNAME
      value
    """
    scr_lines.append(name)
    scr_lines.append(str(value))


with open(input_file, 'r') as f:
    reader = csv.reader(f)
    header = next(reader)#skip header


    # random settings to make the script be able to do everything itself
    add_sysvar("VTENABLE", 0)
    add_sysvar("DYNMODE", 0)
    add_sysvar("CMDECHO", 0)
    add_sysvar("OSMODE", 0)
    add_sysvar("ATTDIA", 0)
    add_sysvar("ATTREQ", 1)
    add_sysvar("DIMJUST",0)
    add_sysvar("DIMTMOVE", 0)
    scr_lines.append("VIEWRES")
    scr_lines.append("Y")
    scr_lines.append("20000")
    scr_lines.append("TEXTSTYLE")
    scr_lines.append("ROMANS")


    START_DRAWING_POSITION = (0,-2500)
    gx, gy = START_DRAWING_POSITION # this is the bottom left hand corner of the current drawing


    #start reading individual flanges here
    for row in reader:

        Type = row[3]
        if Type != "Slip On":
            continue

        Series = float(row[0])
        NPS = float(row[1])
        Schedule = row[2]
        RF_OD = float(row[4]) #raised face OD
        h = float(row[5])     #face step height
        O = float(row[6])     #OD of flange
        W = float(row[7])     #Bolt circle diameter
        d = float(row[9])     #bolt hole diameter (mm)
        n = int(row[10])      #number of bolts
        bolt_spec_imperial = row[11]
        bolt_spec_metric = row[12]
        L = float(row[13])    #stud bolt length
        tf = float(row[14])   #flange thickness
        X = float(row[15])    #hub diameter
        A_h = float(row[16])  #Neck chamfer
        Y = float(row[17])
        B = float(row[19])

        bore_to_spec = False
        if B == -999:
            bore_to_spec = True
            B = A_h-10

        scales = [1, 2, 2.5, 4, 5, 10, 15, 20]
        
        #find a scale which fits in the space
        dimscale = 1  # Default to 1:1
        for scale in scales:
            if O / scale <= 115.0:
                dimscale = scale
                break
        
        #set global dimscale to the correct one
        add_sysvar("DIMSCALE", dimscale)
        add_sysvar("LTSCALE", 1/dimscale)

        gx += 200*dimscale # update in halves like this so it looks pretty 

        sx = gx + 105*dimscale
        sy = gy + 220*dimscale

        # Calculate points with startpos offset
        """
        #OLD POINTS
        A =  (sx,         sy)
        B  = (sx + 0,     sy + OD / 2)
        C  = (sx + b - h1, sy + OD / 2)
        D = (sx + b - h1, sy + (D1 / 2) + d / 2)  
        E  = (sx + 0,     sy + (D1 / 2) + d / 2)
        F  = (sx + b - h1, sy + (D1 / 2) - d / 2)
        G  = (sx + 0,     sy + (D1 / 2) - d / 2)
        H  = (sx + 0,     sy + d_b / 2)
        I  = (sx + b,     sy + d_b / 2)
        J  = (sx + b,     sy + D4 / 2)
        K  = (sx + b - h1, sy + D4 / 2)
        L =  (sx + b,     sy)
        S =  (sx + b - H_0, sy + d_b/2)
        T =  (sx + b - H_0, sy + d_b/2+1)
        U =  (sx + b - H_0 + (Dn/2 - d_b/2 - 1)/3**0.5, sy + Dn/2)
        V =  (sx + b - H_0 + H1, sy + Dn/2)
        W =  (sx,          sy + Dm/2)
        """

        #NEW POINTS
        pA = (sx -(-tf -h),  sy)
        pB = (sx -(-tf -h),  sy + B/2)
        pC = (sx -(-tf -h),  sy + RF_OD/2)
        pD = (sx -(-tf  ),   sy + RF_OD/2)
        pE = (sx -(-tf  ),   sy + W/2 - d/2)
        pF = (sx -(-tf  ),   sy + W/2 + d/2)
        pG = (sx -(-tf  ),   sy + O/2)
        pH = (sx -(-tf +tf), sy + O/2)
        pI = (sx -(-tf +tf), sy + W/2 + d/2)
        pJ = (sx -(-tf +tf), sy + W/2 - d/2)
        pK = (sx -(-tf +tf), sy + X/2)
        pL = (sx -(-tf +tf), sy + A_h/2)
        pM = (sx -(-tf + Y - ((A_h-B)/2 -2)*math.tan((math.pi/180)*37.5) ),sy + A_h/2)
        pN = (sx -(-tf + Y),  sy + B/2 + 2)
        pO = (sx -(-tf + Y),  sy + B/2)
        pP = (sx -(-tf + Y),  sy)
        pQ = (sx -(-tf + tf), sy + B/2)
        pR = (sx -(-tf + tf), sy)

        """
        mappings:
        H -> unused
        L -> pA
        I -> pB
        J -> pC
        K -> pD
        F -> pE
        D -> pF
        C -> pG
        B -> pH
        E -> pI
        G -> pJ
        W -> pK
        V -> pL
        U -> pM
        T -> pN
        S -> pO
        """


# Collect ALL X and Y coordinates to find the true bounding box
        all_x = [pA[0], pB[0], pC[0], pD[0], pE[0], pF[0], pG[0], pH[0], pI[0], pJ[0], pK[0], pL[0], pM[0], pN[0], pO[0], pP[0]]
        all_y = [pA[1], pB[1], pC[1], pD[1], pE[1], pF[1], pG[1], pH[1], pI[1], pJ[1], pK[1], pL[1], pM[1], pN[1], pO[1], pP[1]]
        
        min_x = min(all_x)
        max_x = max(all_x)
        min_y = min(all_y)
        max_y = max(all_y)

        # Pad the box by 1 unit on all sides
        sel_x1 = min_x - 1
        sel_y1 = min_y - 1
        sel_x2 = max_x + 1
        sel_y2 = max_y + 1

        # Zoom to the area for this flange (Using the fixed mirror formula)
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        lower_y = 2 * sy - (max_y + 1)
        scr_lines.append(fmt((sel_x1, lower_y)))
        scr_lines.append(fmt((sel_x2, sel_y2)))

        #Change to 0 layer
        scr_lines.append("CLAYER")
        scr_lines.append("0")

        #Write title 
        scr_lines.append("TEXT")
        scr_lines.append(fmt((gx+75, gy + 305*dimscale)))
        scr_lines.append(f"{20*dimscale}")
        scr_lines.append("0")
        scr_lines.append(f"""{Type}""")
        scr_lines.append("\n\n")

        scr_lines.append("TEXT")
        scr_lines.append(fmt((gx, gy + 335*dimscale)))
        scr_lines.append(f"{20*dimscale}")
        scr_lines.append("0")
        scr_lines.append(f"""#{Series} NPS {NPS}" """)
        scr_lines.append("\n\n")

        #--- Draw line segments
        line(pB,pC,pD,pE,pJ,pK,pQ,pB)
        line(pF,pG,pH,pI)
        line(pB,pA)
        line(pQ,pR)
        line(pF, pE)
        line(pI,pJ)

        #Change to DIM layer
        scr_lines.append("CLAYER")
        scr_lines.append("DIM")
        
        # Hatching 
        add_sysvar("HPNAME", "ANSI31")
        add_sysvar("HPSCALE", 10*dimscale)
        add_sysvar("HPANG", 0)

        scr_lines.append("-HATCH")
        scr_lines.append(fmt(midpoint(pH,pG,pF,pI)))
        scr_lines.append(fmt(midpoint(pE,pJ,pB)))
        scr_lines.append("")   
        

        # --- Mirror 
        scr_lines.append("MIRROR")
        scr_lines.append("C")                          # Crossing selection
        scr_lines.append(fmt((sel_x1, sel_y1)))         # First corner
        scr_lines.append(fmt((sel_x2, sel_y2)))         # Opposite corner
        scr_lines.append("")                            # Enter to end selection
        scr_lines.append(fmt((sx, sy)))                  # First point of mirror line (x-axis)
        scr_lines.append(fmt((sx + 1, sy)))              # Second point of mirror line
        scr_lines.append("N")                           # Don't erase source objects

        # Centerlines 
        #Change to centerline layer
        scr_lines.append("CLAYER")
        scr_lines.append("CENTER")
        add_sysvar("CELWEIGHT", 5) #scale centerline weight, scale, extension
        add_sysvar("CENTERLTSCALE", 25*dimscale)
        add_sysvar("CENTEREXE", 1.0*dimscale)

        #zoom in so it doesn't get fucked up
        add_sysvar("PICKBOX", 1)
        groove_margin = 2
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((pI[0] - groove_margin, pJ[1] - groove_margin)))
        scr_lines.append(fmt((pF[0] + groove_margin, pF[1] + groove_margin)))

        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(pI, pF)))
        scr_lines.append(fmt(midpoint(pJ, pE)))

        # bottom half
        cpI = conjugate(pI); cpF = conjugate(pF)
        cpJ = conjugate(pJ); cpE = conjugate(pE)
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((cpI[0] - groove_margin, min(cpI[1], cpJ[1]) - groove_margin)))
        scr_lines.append(fmt((cpF[0] + groove_margin, max(cpF[1], cpJ[1]) + groove_margin)))

        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(cpI, cpF)))
        scr_lines.append(fmt(midpoint(cpJ, cpE)))

        # main centerline
        cpO = conjugate(pO); cpB = conjugate(pB)
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((pO[0] - groove_margin, min(pO[1], cpO[1]) - groove_margin)))
        scr_lines.append(fmt((pB[0] + groove_margin, max(pO[1], cpO[1]) + groove_margin)))

        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(pO, pB)))
        scr_lines.append(fmt(midpoint(cpO, cpB)))

        #zoom back out
        add_sysvar("PICKBOX", 3)
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((sel_x1, 2*sy-(max_y + 1))))
        scr_lines.append(fmt((sel_x2, sel_y2)))
        
        #reset to default for hatch and dims
        add_sysvar("CELWEIGHT", -1) 
        add_sysvar("CELTSCALE", 1)

        ###
        scr_lines.append("CLAYER") # switch back 
        scr_lines.append("DIM")


        # DIMS
        SPACING = 6.5*dimscale

        # main symmetric
        symmetric_diameter_dim(pB, SPACING, pA)
        symmetric_diameter_dim(pC, 2*SPACING, pA)
        symmetric_diameter_dim(midpoint(pF,pE),3*SPACING, pA)
        symmetric_diameter_dim(pG,4*SPACING, pA)

        # bolt 
        scr_lines.append("DIMLINEAR")
        scr_lines.append(fmt(pI))
        scr_lines.append(fmt(pJ)) 
        scr_lines.append("T") # text edit 
        scr_lines.append(f"""%%c<>\X{n} holes""") 
        temp = midpoint(pO,conjugate(pO))
        scr_lines.append(fmt(((temp[0]-5*SPACING),(temp[1])))) 


        # thickness b and h, and little one H1
        scr_lines.append("DIMLINEAR") 
        scr_lines.append(fmt(conjugate(pH))) # flange body thickness, excluding neck
        scr_lines.append(fmt(conjugate(pG))) 
        temp = midpoint(conjugate(pH),conjugate(pG))
        scr_lines.append(fmt(((temp[0]),(temp[1]-2*SPACING)))) 

        scr_lines.append("DIMLINEAR")
        scr_lines.append(fmt(conjugate(pG))) #chamfer dim
        scr_lines.append(fmt(conjugate(pC))) 
        temp = (conjugate(pG)[0], conjugate(pG)[1])
        scr_lines.append(fmt(((temp[0]),(temp[1]-1*SPACING)))) 
        

        # global roughness 
        SIDELENGTH = 3.5*dimscale
        scr_lines.append("TEXT")
        p = (gx+165*dimscale, gy+282.675*dimscale)
        scr_lines.append(fmt(p))
        scr_lines.append(f"{3.5*dimscale}")
        scr_lines.append("0")
        scr_lines.append("Rz 100")
        scr_lines.append("\n\n")

        #symbols
        draw_roughness_symbol((p[0] + 24.75*dimscale, p[1]), SIDELENGTH)
        draw_check_mark((p[0] + 33*dimscale, p[1]), SIDELENGTH*1.25)

        # leaders
        #leader1
        scr_lines.append("LEADER")
        scr_lines.append(fmt(midpoint(pD,pC)))
        q = (p[0]-30*dimscale,p[1]-1*dimscale)
        scr_lines.append(fmt(q))
        scr_lines.append("")
        scr_lines.append("Ra 25")
        scr_lines.append("")

        # roughness symbol (face1)
        r = (q[0]+20*dimscale,q[1]+1.25*dimscale)
        draw_roughness_symbol(r, SIDELENGTH)

        #leader2
        scr_lines.append("LEADER")
        scr_lines.append(fmt(midpoint(pB,pC)))
        q = (p[0],p[1]-2*SPACING)
        scr_lines.append(fmt(q))
        scr_lines.append("")
        scr_lines.append("Ra 12,5")
        scr_lines.append("")

        # roughness symbol (face2)
        r = (q[0]+25*dimscale,q[1]+1.25*dimscale)
        draw_roughness_symbol(r, SIDELENGTH)

        # bolt spec 
        scr_lines.append("-MTEXT")  
        scr_lines.append(fmt((gx + 34*dimscale, gy+180*dimscale))) # First corner
        scr_lines.append("H") # Trigger height option
        scr_lines.append(f"{3*dimscale}") # Specify height
        scr_lines.append("@0,0")  # Opposite corner (relative 0,0 forces no text wrapping)
        scr_lines.append(f"""\W0.75;Studbolt Size: {bolt_spec(bolt_spec_imperial)[0]}" UNC""") # Line 1
        scr_lines.append(f"""\W0.75;or {bolt_spec(bolt_spec_imperial)[1]} x {L} Long""") # Line 2
        scr_lines.append("")  

        # dimbreak - auto break crossing dims
        scr_lines.append("DIMBREAK")
        scr_lines.append("M")
        scr_lines.append("C")
        scr_lines.append(fmt((sel_x1, 2*sy-(max_y + 1))))
        scr_lines.append(fmt((sel_x2, sel_y2)))
        scr_lines.append("")
        scr_lines.append("A")

        #drawing template
        scr_lines.append("-INSERT")
        scr_lines.append("asme_flange_template")  
        scr_lines.append(fmt((gx, gy))) # corner in bottom left at relative 0,0     
        
        #scale it
        scr_lines.append(str(dimscale))            # x
        scr_lines.append(str(dimscale))            # Y 
        scr_lines.append("0")       # rotation

        #attributes
        scr_lines.append(f"""{NPS:g}", CL{Series:g}, RF, SO, [material], B16.5""")
        scr_lines.append(f"""{NPS:g}", CL{Series:g}, RF, SO, [материал], B16.5""")
        scr_lines.append(f"1:{dimscale}")    #scale
        scr_lines.append(f"Маркировку фланца выполнить согласно MSS SP-25")
        scr_lines.append(f"Flange marking in accordance with MSS SP-25 /")


        #name
        scr_lines.append("TEXT")
        scr_lines.append(fmt((gx-0*dimscale, gy-5*dimscale)))
        scr_lines.append(f"{3.5*dimscale}")
        scr_lines.append("0")
        scr_lines.append("K. Flores")
        scr_lines.append("\n\n")

        # Update startpos for next shape
        gx += 200*dimscale
    

            
    #type label
    scr_lines.append("TEXT")
    scr_lines.append(fmt(START_DRAWING_POSITION))
    scr_lines.append(f"{150}")
    scr_lines.append("90")
    scr_lines.append("Slip On")
    scr_lines.append("\n\n")


    scr_lines.append("ZOOM")
    scr_lines.append("E")
    # Restore defaults
    add_sysvar("CMDECHO", 1)
    add_sysvar("DYNMODE", 3)
    add_sysvar("OSMODE", 4133)

# Write .scr file
#join with newlines
with open(output_file, 'a', encoding='utf-8') as f:
    f.write('\n'.join(scr_lines))
    f.write('\n')  # Single trailing newline to execute the last command
