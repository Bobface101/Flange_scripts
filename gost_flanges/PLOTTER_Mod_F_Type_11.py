## For Mod B., Type 11 GOST flanges
import math
import csv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'Type_11_data.csv')
output_file = os.path.join(script_dir, 'commands.scr')
scr_lines = []

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

    # Check mark
    scr_lines.append("LINE")
    scr_lines.append(fmt((x - 0.3 * s, y + 0.5 * s)))
    scr_lines.append(fmt((x - 0.1 * s, y + 0.3 * s)))
    scr_lines.append(fmt((x + 0.4 * s, y + 0.8 * s)))
    scr_lines.append("")

    #brackets
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


    START_DRAWING_POSITION = (0,-50000)
    gx, gy = START_DRAWING_POSITION # this is the bottom left hand corner of the current drawing

    #start reading individual flanges here
    for row in reader:
        # Flange,Dm,Dn,d1(d_b),b,H,H1 (H_0),OD,D1,d,n,Bolt_Size,D2,h
        print(f"row0: {row[0]}, row1:{row[1]}")
        flange = row[0]
        Dm = float(row[1])
        Dn = float(row[2])
        d_b   = float(row[3])
        b  = float(row[4])
        H_0 = float(row[5]) #rename to H_0 because of coordinate name
        H1 = float(row[6])
        OD  = float(row[7])
        D1 = float(row[8])
        d   = float(row[9])
        n   = int(row[10])
        bolt_size   = row[11]
        D2   = float(row[12])
        h = float(row[13])
        h1 = float(row[14])
        h2 = float(row[15])
        D6 = float(row[17])

        gost_scales = [1, 2, 2.5, 4, 5, 10, 15, 20]
        
        #find a scale which fits in the space
        dimscale = 1  # Default to 1:1
        for scale in gost_scales:
            if OD / scale <= 115.0:
                dimscale = scale
                break
        
        #set global dimscale to the correct one
        add_sysvar("DIMSCALE", dimscale)
        add_sysvar("LTSCALE", 1/dimscale)

        gx += 200*dimscale # update in halves like this so it looks pretty 

        sx = gx + 105*dimscale
        sy = gy + 220*dimscale

        # Calculate points with startpos offset
        A =  (sx,         sy)
        B  = (sx + 0,     sy + OD / 2)
        C  = (sx + b - h, sy + OD / 2)
        D = (sx + b - h, sy + (D1 / 2) + d / 2)  
        E  = (sx + 0,     sy + (D1 / 2) + d / 2)
        F  = (sx + b - h, sy + (D1 / 2) - d / 2)
        G  = (sx + 0,     sy + (D1 / 2) - d / 2)
        H  = (sx + 0,     sy + d_b / 2)
        I  = (sx + b,     sy + d_b / 2)
        J  = (sx + b,     sy + D2 / 2)
        K  = (sx + b - h, sy + D2 / 2 + h)
        L =  (sx + b,     sy)
        O =  (sx + b,      sy + D6 / 2)
        P =  (sx + b - h1, sy + D6 / 2)
        Q =  (sx + b - h1, sy + d_b / 2)
        R =  (sx + b - h1, sy)
        S =  (sx + b - H_0, sy + d_b/2)
        T =  (sx + b - H_0, sy + d_b/2+1)
        U =  (sx + b - H_0 + (Dn/2 - d_b/2 - 1)/3**0.5, sy + Dn/2)
        V =  (sx + b - H_0 + H1, sy + Dn/2)
        W =  (sx,          sy + Dm/2)


# Collect ALL X and Y coordinates to find the true bounding box
        all_x = [A[0], B[0], C[0], D[0], E[0], F[0], G[0], H[0], I[0], J[0], K[0], L[0], S[0], T[0], U[0], V[0], W[0]]
        all_y = [A[1], B[1], C[1], D[1], E[1], F[1], G[1], H[1], I[1], J[1], K[1], L[1], S[1], T[1], U[1], V[1], W[1]]
        
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
        scr_lines.append(f"{flange}")
        scr_lines.append("\n\n")

        #--- Draw line segments

        # flange neck here
        scr_lines.append("LINE")   
        scr_lines.append(fmt(S))
        scr_lines.append(fmt(T))
        scr_lines.append(fmt(U))
        scr_lines.append(fmt(V))
        scr_lines.append(fmt(W))
        scr_lines.append("") 

        #  W -> B -> C -> D -> E
        scr_lines.append("LINE")
        scr_lines.append(fmt(W))
        scr_lines.append(fmt(B))
        scr_lines.append(fmt(C))
        scr_lines.append(fmt(D))
        scr_lines.append(fmt(E))
        scr_lines.append("")  # Enter to end LINE command

        #  G -> F
        scr_lines.append("LINE")
        scr_lines.append(fmt(G))
        scr_lines.append(fmt(F))
        scr_lines.append("")  # Enter to end LINE command

       #  D  -> K -> J -> I -> S -> axis
        scr_lines.append("LINE")
        scr_lines.append(fmt(D))
        scr_lines.append(fmt(K))
        scr_lines.append(fmt(J))
        scr_lines.append(fmt(O))
        scr_lines.append(fmt(P))
        scr_lines.append(fmt(Q))
        scr_lines.append(fmt(S))
        scr_lines.append((fmt((S[0],sy))))
        scr_lines.append("")  # Enter to end LINE command

        #  O -> L 
        scr_lines.append("LINE")
        scr_lines.append(fmt(O))
        scr_lines.append(fmt(L))
        scr_lines.append("")  # Enter to end LINE command

        #  R -> Q
        scr_lines.append("LINE")
        scr_lines.append(fmt(R))
        scr_lines.append(fmt(Q))
        scr_lines.append("")  # Enter to end LINE command

       
        overlap = K[1] - F[1] # need to draw a small line if the bore intersects the chamfer
        if overlap > 0:
            scr_lines.append("LINE")
            scr_lines.append(fmt(F))
            scr_lines.append(f"@{overlap},0")
            scr_lines.append("") 

        #Fillets

        FILLET_RADIUS = lengthof(V, W)/3.5 # I chose 3.5 empirically determined from COMPASS
        FILLET_RADIUS = round(2*FILLET_RADIUS)/2 # round to nearest 0.5

        scr_lines.append("FILLET")
        scr_lines.append(fmt(midpoint(U,V)))
        scr_lines.append("RADIUS")
        scr_lines.append(f"{FILLET_RADIUS}")
        scr_lines.append(fmt(midpoint(V,W)))

        scr_lines.append("FILLET")
        scr_lines.append(fmt(midpoint(V,W)))
        scr_lines.append("RADIUS")
        scr_lines.append(f"{FILLET_RADIUS}")
        scr_lines.append(fmt(midpoint(W,G)))
        


        #Change to DIM layer
        scr_lines.append("CLAYER")
        scr_lines.append("DIM")
        
        # Hatching 
        add_sysvar("HPNAME", "ANSI31")
        add_sysvar("HPSCALE", 10*dimscale)
        add_sysvar("HPANG", 0)

        scr_lines.append("-HATCH")
        scr_lines.append(fmt(midpoint(B,C,D,E)))
        scr_lines.append(fmt(midpoint(F,G,H,I)))
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
        scr_lines.append(fmt((E[0] - groove_margin, G[1] - groove_margin)))
        scr_lines.append(fmt((D[0] + groove_margin, D[1] + groove_margin)))

        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(E, D)))
        scr_lines.append(fmt(midpoint(G, F)))

        # bottom half
        cE = conjugate(E); cD = conjugate(D)
        cG = conjugate(G); cF = conjugate(F)
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((cE[0] - groove_margin, min(cE[1], cG[1]) - groove_margin)))
        scr_lines.append(fmt((cD[0] + groove_margin, max(cD[1], cG[1]) + groove_margin)))

        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(cE, cD)))
        scr_lines.append(fmt(midpoint(cG, cF)))

        # main centerline
        cH = conjugate(H); cI = conjugate(I)
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((H[0] - groove_margin, min(H[1], cH[1]) - groove_margin)))
        scr_lines.append(fmt((I[0] + groove_margin, max(H[1], cH[1]) + groove_margin)))

        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(H, I)))
        scr_lines.append(fmt(midpoint(cH, cI)))

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
        symmetric_diameter_dim(Q, 6.5*SPACING, L)
        symmetric_diameter_dim(O, 7.5*SPACING, L)
        symmetric_diameter_dim(J, 8.5*SPACING, L)
        symmetric_diameter_dim(midpoint(D,F),9.5*SPACING, L)
        symmetric_diameter_dim(C,10.5*SPACING, L)
        symmetric_diameter_dim(U, -2*SPACING, S)
        symmetric_diameter_dim(W, b-H_0-3*SPACING, W)

        # bolt 
        scr_lines.append("DIMLINEAR")
        scr_lines.append(fmt(E))
        scr_lines.append(fmt(G)) 
        scr_lines.append("T") # text edit 
        scr_lines.append(f"%%c<> for {bolt_size}\X{n} holes") 
        temp = midpoint(S,conjugate(S))
        scr_lines.append(fmt(((temp[0]-5*SPACING),(temp[1])))) 


        # thickness b and h, h1 and little one H1
        scr_lines.append("DIMLINEAR") 
        scr_lines.append(fmt(conjugate(B))) # flange body thickness b, excluding neck
        scr_lines.append(fmt(conjugate(C))) 
        temp = midpoint(conjugate(B),conjugate(C))
        scr_lines.append(fmt(((temp[0]),(temp[1]-2*SPACING)))) 

        scr_lines.append("DIMLINEAR")
        scr_lines.append(fmt(conjugate(C))) #chamfer dim h
        scr_lines.append(fmt(conjugate(J))) 
        scr_lines.append("T") # text edit 
        scr_lines.append(f"<>x45%%d") 
        temp = (conjugate(C)[0] + h/2, conjugate(C)[1])
        scr_lines.append(fmt(((temp[0]),(temp[1]-1*SPACING)))) 

        scr_lines.append("DIMLINEAR") 
        scr_lines.append(fmt(conjugate(V))) # H1
        scr_lines.append(fmt(conjugate(T))) 
        scr_lines.append(fmt((((T[0]+V[0])/2),(sy-OD/2-SPACING)))) 

        scr_lines.append("DIMLINEAR") 
        scr_lines.append(fmt(conjugate(P))) # h1 face seal depth 
        scr_lines.append(fmt(conjugate(O))) 
        temp = conjugate(midpoint(O,P))
        scr_lines.append(fmt((temp[0],temp[1]+SPACING))) 


        # weld edge lip (neck)
        scr_lines.append("DIMLINEAR")
        scr_lines.append(fmt(T)) #chamfer dim
        scr_lines.append(fmt(S)) 
        scr_lines.append("T") # text edit 
        scr_lines.append("<>{\H0.7x;\S+0,5^-0,0;}") 
        temp = (midpoint(T,S))
        scr_lines.append(fmt(((temp[0]-0.75*SPACING),(temp[1])))) 

        #full flange body
        add_sysvar("DIMTIX", 1)    # 1 = Force text inside the extension lines
        add_sysvar("DIMTAD", 1)    # 1 = Place text Above the line
        add_sysvar("DIMATFIT", 1)
        scr_lines.append("DIMLINEAR") 
        scr_lines.append(fmt((T))) # full flange body
        scr_lines.append(fmt((C))) 
        temp = ((T[0]+C[0])/2,C[1])
        scr_lines.append(fmt(((temp[0]),(temp[1]+SPACING)))) 
        add_sysvar("DIMTAD", 1)    # 1 = Text ALWAYS on top of the line
        add_sysvar("DIMTIX", 0)    # 0 = Allows text to pop outside if space is tight
        add_sysvar("DIMATFIT", 3)  # 3 = "Best Fit" (Kicks text outside if it doesn't fit)
        add_sysvar("DIMJUST", 0)

        # angular dims - arc placement on bisector of acute sector
        add_sysvar("DIMTMOVE", 1)
        arc_r = 1.5 * SPACING

        # first angle at T (neck line vs vertical)
        ray1_angle = math.atan2(U[1] - T[1], U[0] - T[0])
        bisector1 = (ray1_angle + math.pi / 2) / 2
        tight_arc_pt1 = (T[0] + arc_r * math.cos(bisector1),
                         T[1] + arc_r * math.sin(bisector1))

        scr_lines.append("DIMANGULAR")
        scr_lines.append("")                         # bypass line selection
        scr_lines.append(fmt(T))                     # vertex
        scr_lines.append(fmt(midpoint(T, U)))        # endpoint on neck line
        scr_lines.append(fmt((T[0], T[1] + 1)))     # endpoint on vertical
        scr_lines.append("T")
        scr_lines.append("30%%d")
        scr_lines.append(fmt(tight_arc_pt1))

        # move text with leader
        scr_lines.append("DIMTEDIT")
        scr_lines.append("L")
        far_away_pt1 = (T[0] - 3 * SPACING, sy + OD / 2 + 1.5 * SPACING)
        scr_lines.append(fmt(far_away_pt1))

        add_sysvar("DIMTMOVE", 0)

        """
        # --- Second angle: at vertex conjugate(V) (fillet line vs horizontal) ---
        cV = conjugate(V)
        cMid_VW = conjugate(midpoint(V, W))
        
        # 1. CALCULATE THE EXACT ANGLE IN PYTHON
        # Using the rise (Dm-Dn) and run of the flange neck coordinates
        #k = abs(D[0]-V[0])/abs(W[0]-V[0]) # make sure the angle extends up to the face
        k=1
        delta_y = k*abs(W[1] - V[1])
        delta_x = k*abs(W[0] - V[0])
        angle_deg = math.degrees(math.atan2(delta_y, delta_x))
        angle_text = f"{round(angle_deg)}%%d" # Creates the string, e.g., "45%%d"

        # Calculate bisector for arc placement (Your existing logic)
        ray1_angle2 = math.atan2(cMid_VW[1] - cV[1], cMid_VW[0] - cV[0])
        ray2_angle2 = 0.0
        r1 = ray1_angle2 % (2 * math.pi)
        r2 = ray2_angle2 % (2 * math.pi)
        span_ccw = (r1 - r2) % (2 * math.pi)
        span_cw = (r2 - r1) % (2 * math.pi)
        if span_ccw <= span_cw:
            bisector2 = (r2 + span_ccw / 2) % (2 * math.pi)
        else:
            bisector2 = (r1 + span_cw / 2) % (2 * math.pi)

        tight_arc_pt2 = (cV[0] + arc_r * math.cos(bisector2),
                         cV[1] + arc_r * math.sin(bisector2))

        # 2. DRAW DIMANGULAR BUT HIDE ITS TEXT
        scr_lines.append("DIMANGULAR")
        scr_lines.append("")                         
        scr_lines.append(fmt(cV))                    
        scr_lines.append(fmt(cMid_VW))               
        scr_lines.append(fmt((cV[0] + 1, cV[1])))   
        scr_lines.append("T")
        scr_lines.append(" ")                        # A single space makes the text invisible!
        scr_lines.append(fmt(tight_arc_pt2))         

        # 3. DRAW THE PROPER LEADER
        # You can push this coordinate anywhere you want!
        far_away_pt2 = (cV[0] - 1.5 * SPACING, cV[1] - 3 * SPACING)
        add_sysvar("DIMLDRBLK", "_NONE")
        
        scr_lines.append("LEADER")
        scr_lines.append(fmt(tight_arc_pt2))         # Arrowhead starts exactly on the dimension arc
        scr_lines.append(fmt(far_away_pt2))          # The dogleg kicks out here
        scr_lines.append("")                         # Enter to end line selection
        scr_lines.append(angle_text)                 # Inject the mathematically calculated angle!
        scr_lines.append("")
        add_sysvar("DIMLDRBLK", ".")
        """
        # fillet radius leaders - pick arc body, not ghost vertex
        cV = conjugate(V)
        cW = conjugate(W)
        cU = conjugate(U)
        cG = conjugate(G)
        shared_text_location = (cV[0] - 2 * SPACING, sy - OD/2)

        # arc at W (between VW and WG lines)
        arc_W = fillet_arc_mid(cW, cV, cG, FILLET_RADIUS)
        scr_lines.append("LEADER")
        scr_lines.append("NEA")
        scr_lines.append(fmt(arc_W))
        scr_lines.append(fmt(shared_text_location))
        scr_lines.append("")
        scr_lines.append(f"R{FILLET_RADIUS}")
        scr_lines.append("")

        # arc at V (between UV and VW lines)
        arc_V = fillet_arc_mid(cV, cU, cW, FILLET_RADIUS)
        scr_lines.append("LEADER")
        scr_lines.append("NEA")
        scr_lines.append(fmt(arc_V))
        scr_lines.append(fmt(shared_text_location))
        scr_lines.append("")
        scr_lines.append(" ")
        scr_lines.append("")
        scr_lines.append("")
        # leaders

        #leader1
        scr_lines.append("LEADER") # face seal
        scr_lines.append(fmt(midpoint(P,Q)))
        #scr_lines.append(fmt(((midpoint(P,Q))[0]+SPACING*1.25,(midpoint(P,Q))[1])))
        q = (P[0]+SPACING*1,P[1]-4*SPACING)
        scr_lines.append(fmt(q))
        scr_lines.append("")
        scr_lines.append("Ra 12,5")
        scr_lines.append("")

        # roughness symbol (face1)
        SIDELENGTH = 3.5*dimscale
        r = (q[0]+25*dimscale,q[1]+1.25*dimscale)
        draw_roughness_symbol(r, SIDELENGTH)

        #leader2 edge seal
        scr_lines.append("LEADER")
        scr_lines.append(fmt(midpoint(O,P)))
        q = (P[0]+SPACING*2,P[1]-2*SPACING)
        scr_lines.append(fmt(q))
        scr_lines.append("")
        scr_lines.append("Ra 25")
        scr_lines.append("")

        # roughness symbol (edge)
        SIDELENGTH = 3.5*dimscale
        r = (q[0]+20*dimscale,q[1]+1.25*dimscale)
        draw_roughness_symbol(r, SIDELENGTH)


        # global roughness 
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
        scr_lines.append("gost_flange_template")  
        scr_lines.append(fmt((gx, gy))) # corner in bottom left at relative 0,0     
        
        #scale it
        scr_lines.append(str(dimscale))            # x
        scr_lines.append(str(dimscale))            # Y 
        scr_lines.append("0")       # rotation
        
        #attributes
        scr_lines.append(f"{flange[0:5]}, {flange[6:]} Type11 Mod.F - GOST 33259-2015")
        scr_lines.append(f"{flange[0:5]}, {flange[6:]} Тип11 Исп.F - ГОСТ 33259-2015")
        scr_lines.append(f"1:{dimscale}")    #scale
        scr_lines.append(f"{flange[2:5]}-{flange[8:]}-11-F-09G2S GOST 33259-2015")
        
        #name
        scr_lines.append("TEXT")
        scr_lines.append(fmt((gx-0*dimscale, gy-5*dimscale)))
        scr_lines.append(f"{3.5*dimscale}")
        scr_lines.append("0")
        scr_lines.append("K. Flores")
        scr_lines.append("\n\n")

        # Update startpos for next shape
        gx += 200*dimscale
    
    #series label
    scr_lines.append("TEXT")
    scr_lines.append(fmt(START_DRAWING_POSITION))
    scr_lines.append(f"{500}")
    scr_lines.append("90")
    scr_lines.append("Mod. F Type 11")
    scr_lines.append("\n\n")

    # 
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

